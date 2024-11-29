import logging
import sqlite3

import sqlite_vec

from ._config import Config
from ._embed import dims, embedding
from ._singleton import singleton
from ._tokenize import tokenize

config = Config()


@singleton
class SQLiteStore:
    def __init__(self):
        db_filename = config.get("db_name", "core", "database.db")
        db_path = config.data_dir / db_filename
        try:
            self.conn = sqlite3.connect(db_path)
            logging.info(f"已连接到数据库: {db_path}")
        except sqlite3.Error as e:
            logging.error(f"连接数据库失败: {e}")
            raise
        try:
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            logging.info("SQLite 扩展 `sqlite_vec` 加载成功")
        finally:
            self.conn.enable_load_extension(False)

        self._check_versions()
        self.cursor = self.conn.cursor()

    def _check_versions(self):
        """
        获取 SQLite 和 vec 扩展的版本信息。
        :return: SQLite 版本和 vec 扩展版本
        """
        try:
            sqlite_version, vec_version = self.conn.execute("SELECT sqlite_version(), vec_version()").fetchone()
            logging.info(f"SQLite版本：{sqlite_version}, sqlite_vec 版本：{vec_version}")
            return sqlite_version, vec_version
        except sqlite3.Error as e:
            logging.error(f"执行 SQL 失败: {e}")
            raise

    def _check_table(self, vault: str):
        pass

    def create_table(self, vault: str):
        # 创建表
        # 创建数据表
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {vault} (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, partition TEXT, title TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);"
        )
        # 创建全文搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_fts USING fts5(indexed_content);")
        # 创建向量搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_vec USING vec0(embedding FLOAT[{str(dims)}]);")

        """
        # 创建触发器保持表同步
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ai AFTER INSERT ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts(rowid, content, title) VALUES (new.id, new.content, new.title); "
            f"END;"
        )
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ad AFTER DELETE ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts({vault}_fts,rowid, content, title) VALUES ('delete',old.id, old.content, old.title); "
            f"END;"
        )
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_au AFTER UPDATE ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts({vault}_fts,rowid, content, title) VALUES ('delete',old.id, old.content, old.title); "
            f"INSERT INTO {vault}_fts(rowid, content, title) VALUES (new.id, new.content, new.title); "
            f"END;"
        )
        """

        # 提交更改
        self.conn.commit()

    # 批量插入数据
    def insert_row(self, data, vault="Core"):
        logging.debug(f"正在插入数据到数据库: {data}")
        self._check_table(vault)
        self.cursor.execute(f"INSERT INTO {vault} (title, partition, content) VALUES (?,?,?)", data)
        title, _, content = data
        indexed_content = " ".join(tokenize(content) + tokenize(title))
        self.cursor.execute(f"INSERT INTO {vault}_fts (indexed_content) VALUES (?)", (indexed_content,))

        # 提交更改
        self.conn.commit()

    def search_keyword(self, query: str, vault="Core", top_n: int = 5):
        self._check_table(vault)
        self.cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
            (" OR ".join(tokenize(query)), top_n),
        )
        return self.cursor.fetchall()

    def search_vector(self, query: str, vault="Core", top_n: int = 5):
        self._check_table(vault)
        self.cursor.excute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_vec join {vault} on {vault}_vec.rowid={vault}.id WHERE headline_embedding MATCH ? AND k = ? ORDER BY distance;",
            (embedding(query), top_n),
        )
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()