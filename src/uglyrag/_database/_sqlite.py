from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from sqlite3 import Connection, Error
from types import TracebackType

import sqlite_vec
from sqlite_vec import serialize_float32

from ._database import Database


@dataclass
class SQLiteDatebase(Database):
    conn: Connection = field(init=False)

    def __post_init__(self) -> None:
        """
        初始化数据库连接和配置。

        此方法在类实例化后调用，用于初始化与SQLite数据库的连接，
        并配置必要的数据库扩展和函数。
        """
        super().__post_init__()
        self.conn = self._connect_db(self.db_path)

    def __enter__(self) -> Database:
        self._lock.acquire()
        return super().__enter__()

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self._lock.release()
        self.conn.commit()

    def reset(self) -> None:
        """
        重置数据库
        """
        super().reset()
        self.conn.close()
        self.conn = self._connect_db(self.db_path)

    def _connect_db(self, db_path: Path) -> Connection:
        """
        连接到数据库。
        """
        # 连接到 SQLite 数据库
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            logging.debug(f"已连接到数据库: {db_path}")
        except Error as e:
            logging.error(f"连接数据库失败: {e}")
            raise

        self._init_conn(conn)
        return conn

    def _init_conn(self, conn: Connection) -> None:
        # 启用加载 SQLite 扩展
        try:
            conn.enable_load_extension(True)
            try:
                sqlite_vec.load(conn)
                logging.debug("SQLite 扩展 `sqlite_vec` 加载成功")
            except Exception as e:
                logging.error(f"加载 SQLite 扩展 `sqlite_vec` 失败: {e}")
                raise
        finally:
            # 确保禁用扩展加载以保证安全性
            conn.enable_load_extension(False)
            logging.debug("已禁用 SQLite 扩展加载")

        # 检查版本信息
        self._check_versions(conn)
        logging.debug("版本信息检查完成")

        # 重新注册函数
        # 注册一个名为"segment"的SQL函数，用于文本分词
        def segment_func(x: str) -> str:
            return " ".join(self.segment(x))

        conn.create_function("segment", 1, segment_func)
        logging.debug("SQL函数 `segment` 注册成功")

        # 注册一个名为"embedding"的SQL函数，用于生成文本的嵌入表示
        def embedding_func(x: str) -> bytes:
            return serialize_float32(self.embedding(x))

        conn.create_function("embedding", 1, embedding_func)
        logging.debug("SQL函数 `embedding` 注册成功")

    @staticmethod
    def _check_versions(conn: Connection) -> tuple[str, str]:
        """
        获取 SQLite 和 vec 扩展的版本信息。
        :return: SQLite 版本和 vec 扩展版本
        """
        try:
            sqlite_version, vec_version = conn.execute("SELECT sqlite_version(), vec_version()").fetchone()
            logging.debug(f"SQLite版本：{sqlite_version}, sqlite_vec 版本：{vec_version}")
            return sqlite_version, vec_version
        except Error as e:
            logging.error(f"执行 SQL 失败: {e}")
            raise

    def _check_vault(self, vault: str) -> bool:
        cursor = self.conn.cursor()
        if vault.endswith("_fts") or vault.endswith("_vec"):
            logging.warning(f"表名 {vault} 结尾为 _fts 或 _vec，将无法使用。")
            return False
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{vault}'")
            if not bool(cursor.fetchone()):
                self._create_vault(vault, self.conn)
            return True
        except Error as e:
            logging.error(f"检查或创建表失败: {e}")
            return False

    def _create_vault(self, vault: str, conn: Connection) -> None:
        cursor = conn.cursor()
        # 创建表
        # 创建数据表
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {vault} (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, part_id TEXT, source TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);"
        )
        # 创建全文搜索表
        cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_fts USING fts5(indexed_content);")
        # 创建向量搜索表
        cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_vec USING vec0(embedding FLOAT[{self.dims}]);")

        # 创建触发器保持表同步
        cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ai AFTER INSERT ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts(rowid, indexed_content) VALUES (new.id, segment(new.content));"
            f"INSERT INTO {vault}_vec(rowid, embedding) VALUES (new.id, embedding(new.content));"
            f"END;"
        )
        cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ad AFTER DELETE ON {vault} BEGIN "
            f"DELETE FROM {vault}_fts WHERE rowid = old.id;"
            f"DELETE FROM {vault}_vec WHERE rowid = old.id;"
            f"END;"
        )
        cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_au AFTER UPDATE ON {vault} BEGIN "
            f"UPDATE {vault}_fts SET indexed_content = segment(new.content) WHERE rowid = new.id;"
            f"UPDATE {vault}_vec SET embedding = embedding(new.content) WHERE rowid = new.id;"
            f"END;"
        )
        self.conn.commit()

    # 插入数据
    def insert_data(self, data: list[tuple[str, str, str]], vault: str) -> None:
        cursor = self.conn.cursor()
        if not data:
            raise Exception("No content to insert")
        else:
            for doc in data:
                if len(doc) != 3:
                    logging.error(f"Invalid document format: {doc}")
                    raise Exception("Invalid document format")
        cursor.executemany(f"INSERT INTO {vault} (source, part_id, content) VALUES (?,?,?)", data)

    def check_source(self, source: str, vault: str) -> bool:
        if not self.check_vault(vault):
            raise Exception("No such vault")
        result = self.conn.execute(f"SELECT EXISTS(SELECT 1 FROM {vault} WHERE source=?)", (source,)).fetchone()
        assert result is not None
        return result[0] == 1

    def del_source(self, source: str, vault: str) -> bool:
        if not self.check_vault(vault):
            raise Exception("No such vault")
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {vault} WHERE source=?", (source,))
            self.conn.commit()
            return True
        except Error as e:
            logging.error(f"删除数据失败: {e}")
            return False

    def _background_search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
            (" OR ".join(self.segment(query)), top_n),
        )
        '''
        # TODO: 如果希望对相同来源的文档召回的数量进行限制，可以用下面的方法，具体代码还需要进一步修改
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
        return cursor.fetchall()

    def _background_search_vec(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_vec join {vault} on {vault}_vec.rowid={vault}.id WHERE embedding MATCH ? AND k = ? ORDER BY distance;",
            (serialize_float32(self.embedding(query)), top_n),
        )
        return cursor.fetchall()
