from __future__ import annotations

import logging
from dataclasses import dataclass, field
from sqlite3 import Connection, Cursor, Error, connect

import sqlite_vec
from sqlite_vec import serialize_float32

from uglyrag._config import config

from ._db_impl import Database

db_filename = config.get("db_name", default="database.db")
db_path = config.data_dir / db_filename


@dataclass
class SQLiteStore(Database):
    conn: Connection = field(init=False)
    cursor: Cursor = field(init=False)

    def __post_init__(self):
        """
        初始化数据库连接和配置。

        此方法在类实例化后调用，用于初始化与SQLite数据库的连接，
        并配置必要的数据库扩展和函数。
        """
        if not db_path.name.endswith(".db"):
            raise ValueError("无效的数据库文件路径，必须以 .db 结尾")

        try:
            # 连接到 SQLite 数据库
            self.conn = connect(db_path)
            logging.debug(f"已连接到数据库: {db_path}")
        except Error as e:
            logging.error(f"连接数据库失败: {e}")
            raise

        try:
            # 启用加载 SQLite 扩展
            self.conn.enable_load_extension(True)
            try:
                sqlite_vec.load(self.conn)
                logging.debug("SQLite 扩展 `sqlite_vec` 加载成功")
            except Exception as e:
                logging.error(f"加载 SQLite 扩展 `sqlite_vec` 失败: {e}")
                raise
        finally:
            # 确保禁用扩展加载以保证安全性
            self.conn.enable_load_extension(False)
            logging.debug("已禁用 SQLite 扩展加载")

        # 检查版本信息
        self._check_versions()
        logging.debug("版本信息检查完成")

        # 创建游标对象用于执行 SQL 命令
        self.cursor = self.conn.cursor()
        logging.debug("游标对象创建成功")

        # 重新注册函数
        # 注册一个名为"segment"的SQL函数，用于文本分词
        def segment_func(x):
            return " ".join(self.segment(x))

        self.conn.create_function("segment", 1, segment_func)
        logging.debug("SQL函数 `segment` 注册成功")

        # 注册一个名为"embedding"的SQL函数，用于生成文本的嵌入表示
        def embedding_func(x):
            return serialize_float32(self.embedding(x))

        self.conn.create_function("embedding", 1, embedding_func)
        logging.debug("SQL函数 `embedding` 注册成功")

    def _check_versions(self):
        """
        获取 SQLite 和 vec 扩展的版本信息。
        :return: SQLite 版本和 vec 扩展版本
        """
        try:
            sqlite_version, vec_version = self.conn.execute("SELECT sqlite_version(), vec_version()").fetchone()
            logging.debug(f"SQLite版本：{sqlite_version}, sqlite_vec 版本：{vec_version}")
            return sqlite_version, vec_version
        except Error as e:
            logging.error(f"执行 SQL 失败: {e}")
            raise

    def check_vault(self, vault: str) -> bool:
        if vault.endswith("_fts") or vault.endswith("_vec"):
            logging.warning(f"表名 {vault} 结尾为 _fts 或 _vec，将无法使用。")
            return False
        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{vault}'")
            if not bool(self.cursor.fetchone()):
                self._create_table(vault)
            return True
        except Error as e:
            logging.error(f"检查或创建表失败: {e}")
            return False

    def _create_table(self, vault: str):
        # 创建表
        # 创建数据表
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {vault} (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, part_id TEXT, source TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);"
        )
        # 创建全文搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_fts USING fts5(indexed_content);")
        dims = len(self.embedding("Hello"))
        # 创建向量搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_vec USING vec0(embedding FLOAT[{str(dims)}]);")
        logging.debug(f"向量表维度为：{dims}")
        self._create_trigger(vault)

        # 提交更改
        self.conn.commit()

    def _create_trigger(self, vault: str):
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
    def insert_data(self, data: tuple[str], vault: str):
        if not self.check_vault(vault):
            raise Exception("No such vault")

        if not data:
            raise Exception("No content to insert")
        elif not isinstance(data, tuple) or len(data) != 3:
            raise Exception("Invalid document format")
        self.cursor.execute(f"INSERT INTO {vault} (source, part_id, content) VALUES (?,?,?)", data)
        logging.debug(f"已插入数据: {data}")

        # 提交更改
        self.conn.commit()

    def check_source(self, source: str, vault: str) -> bool:
        if not self.check_vault(vault):
            return False
        return self.cursor.execute(f"SELECT EXISTS(SELECT 1 FROM {vault} WHERE source=?)", (source,)).fetchone()[0] == 1

    def rm_source(self, source: str, vault: str):
        if not self.check_vault(vault):
            raise Exception("No such vault")
        self.cursor.execute(f"DELETE FROM {vault} WHERE source=?", (source,))
        self.conn.commit()

    def search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        self.cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
            (" OR ".join(self.segment(query)), top_n),
        )
        '''
        # 如果希望对相同来源的文档召回的数量进行限制，可以用下面的方法，具体代码还需要进一步修改
        self.cursor.execute(
            f"""
            SELECT id, content
            FROM (
                SELECT
                    {vault}.id,
                    {vault}.content,
                    {vault}.source,
                    ROW_NUMBER() OVER (PARTITION BY {vault}.source ORDER BY bm25({vault}_fts)) as rn_source,
                    ROW_NUMBER() OVER (ORDER BY bm25({vault}_fts)) as rn_total
                FROM
                    {vault}_fts
                JOIN
                    {vault}
                ON
                    {vault}_fts.rowid = {vault}.id
                WHERE
                    {vault}_fts MATCH ?
            ) subquery
            WHERE rn_source <= ？ AND rn_total <= ?
            """,
            (" OR ".join(self.segment(query)), 5, top_n),
        )
        '''
        return self.cursor.fetchall()

    def search_vec(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        self.cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_vec join {vault} on {vault}_vec.rowid={vault}.id WHERE embedding MATCH ? AND k = ? ORDER BY distance;",
            (serialize_float32(self.embedding(query)), top_n),
        )
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()
