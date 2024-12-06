import logging
import sqlite3
from dataclasses import dataclass, field
from sqlite3 import Connection, Cursor
from typing import Callable, List, Tuple

import sqlite_vec

from uglyrag._config import config

db_filename = config.get("db_name", "DEFAULT", "database.db")
db_path = config.data_dir / db_filename


@dataclass
class SQLiteStore:
    segment: Callable[[str], List[str]]
    embedding: Callable[[str], List[float]]
    conn: Connection = field(init=False)
    cursor: Cursor = field(init=False)

    def __post_init__(self):
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

    def check_table(self, vault: str) -> bool:
        if vault.endswith("_fts") or vault.endswith("_vec"):
            logging.warning(f"表名 {vault} 结尾为 _fts 或 _vec，将无法使用。")
            return False
        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{vault}'")
            if not bool(self.cursor.fetchone()):
                self.create_table(vault)
            return True
        except sqlite3.Error as e:
            logging.error(f"检查或创建表失败: {e}")
            return False

    def create_table(self, vault: str):
        # 创建表
        # 创建数据表
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {vault} (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, chunk_index TEXT, path TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);"
        )
        # 创建全文搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_fts USING fts5(indexed_content);")
        dims = len(self.embedding("Hello"))
        # 创建向量搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_vec USING vec0(embedding FLOAT[{str(dims)}]);")
        logging.debug(f"向量表维度为：{dims}")
        self.create_trigger(vault)

        # 提交更改
        self.conn.commit()

    def create_trigger(self, vault: str):
        self.conn.create_function("segment", 1, lambda x: " ".join(self.segment(x)))
        self.conn.create_function("embedding", 1, self.embedding)
        # 创建触发器保持表同步
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ai AFTER INSERT ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts(rowid, indexed_content) VALUES (new.id, segment(new.content));"
            f"INSERT INTO {vault}_vec(rowid, embedding) VALUES (new.id, embedding(new.content));"
            f"END;"
        )
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ad AFTER DELETE ON {vault} BEGIN "
            f"DELETE FROM {vault}_fts WHERE rowid = old.id;"
            f"DELETE FROM {vault}_vec WHERE rowid = old.id;"
            f"END;"
        )
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_au AFTER UPDATE ON {vault} BEGIN "
            f"UPDATE {vault}_fts SET indexed_content = segment(new.content) WHERE rowid = new.id;"
            f"UPDATE {vault}_vec SET embedding = embedding(new.content) WHERE rowid = new.id;"
            f"END;"
        )

    # 插入数据
    def insert_row(self, doc: str | Tuple[str], vault: str = "Core"):
        if not self.check_table(vault):
            raise Exception("No such vault")

        if not doc:
            raise Exception("No content to insert")
        elif isinstance(doc, str):
            doc = (None, None, doc)
        elif isinstance(doc, tuple) and len(doc) == 3:
            pass
        else:
            raise Exception("Invalid document format")
        logging.debug(f"正在插入数据到数据库: {doc}")
        self.cursor.execute(f"INSERT INTO {vault} (path, chunk_index, content) VALUES (?,?,?)", doc)

        # 提交更改
        self.conn.commit()

    def search_fts(self, query: str, vault="Core", top_n: int = 5) -> List[Tuple[str, str]]:
        self.cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
            (" OR ".join(self.segment(query)), top_n),
        )
        return self.cursor.fetchall()

    def search_vec(self, query: str, vault="Core", top_n: int = 5) -> List[Tuple[str, str]]:
        self.cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_vec join {vault} on {vault}_vec.rowid={vault}.id WHERE embedding MATCH ? AND k = ? ORDER BY distance;",
            (self.embedding(query), top_n),
        )
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()
