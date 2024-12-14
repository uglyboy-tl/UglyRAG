from __future__ import annotations

import logging
from dataclasses import dataclass, field

from duckdb import DuckDBPyConnection, Error, connect, list_type
from duckdb.typing import FLOAT, VARCHAR

from uglyrag._config import config

from ._database import Database

db_filename: str = config.get("db_name", default="database.ddb")
db_path = config.data_dir / db_filename


@dataclass
class DuckDBStore(Database):
    conn: DuckDBPyConnection = field(init=False)
    dims: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not db_path.name.endswith(".ddb"):
            raise ValueError("无效的数据库文件路径，必须以 .ddb 结尾")

        self.conn = self._connect_db()

    def _connect_db(self) -> DuckDBPyConnection:
        # 连接到 DuckDB 数据库
        try:
            conn = connect(db_path, config={"hnsw_enable_experimental_persistence": 1})
            logging.debug(f"已连接到数据库: {db_path}")
        except Error as e:
            logging.error(f"连接数据库失败: {e}")
            raise

        # 安装和加载 DuckDB 扩展
        try:
            """# fts 扩展会被自动加载
            conn.install_extension("fts")
            conn.load_extension("fts")
            logging.debug("DuckDB 扩展 `fts` 安装成功")
            """
            conn.install_extension("vss")
            conn.load_extension("vss")
            logging.debug("DuckDB 扩展 `vss` 安装成功")
        except Error as e:
            logging.error(f"安装 DuckDB 扩展失败: {e}")
            raise

        # 重新注册函数
        # 注册一个名为"segment"的SQL函数，用于文本分词
        def segment_func(x: str) -> str:
            return " ".join(self.segment(x))

        conn.create_function("segment", segment_func, [VARCHAR], VARCHAR)
        logging.debug("SQL函数 `segment` 注册成功")

        conn.create_function("embedding", self.embedding, [VARCHAR], list_type(FLOAT))
        logging.debug("SQL函数 `embedding` 注册成功")

        return conn

    def reset(self) -> None:
        return

    def check_vault(self, vault: str) -> bool:
        """
        检查数据库是否存在，不存在则创建
        """
        if vault.endswith("_fts") or vault.endswith("_vec"):
            logging.warning(f"表名 {vault} 结尾为 _fts 或 _vec，将无法使用。")
            return False
        try:
            self.conn.execute(f"SELECT * FROM information_schema.tables WHERE table_name='{vault}'")
            if not bool(self.conn.fetchone()):
                self._create_table(vault)
            return True
        except Error as e:
            logging.error(f"检查或创建表失败: {e}")
            return False

    def _create_table(self, vault: str) -> None:
        # 创建表
        # 创建数据表
        self.conn.execute(
            f"CREATE TABLE IF NOT EXISTS {vault} (id INTEGER PRIMARY KEY, content TEXT NOT NULL, content_fts TEXT NOT NULL, content_vec FLOAT[{self.dims}], part_id TEXT, source TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        # 创建自增ID列
        self.conn.execute("CREATE SEQUENCE seq_id START 1;")
        # 创建向量搜索索引
        self.conn.execute(f"CREATE INDEX {vault}_vec_index ON {vault} USING HNSW (content_vec);")

    def _background_insert(self, data: tuple[str, str, str], vault: str) -> None:
        """
        插入数据
        """
        if not self.check_vault(vault):
            raise Exception("No such vault")

        if not data:
            raise Exception("No content to insert")
        elif not isinstance(data, tuple) or len(data) != 3:
            raise Exception("Invalid document format")
        source, part_id, content = data
        content_fts = " ".join(self.segment(content))
        content_vec = self.embedding(content)
        new_data = (source, part_id, content, content_fts, content_vec)
        self.conn.execute(
            f"INSERT INTO {vault} (id,source, part_id, content, content_fts, content_vec) VALUES (nextval('seq_id'),?,?,?,?,?)",
            new_data,
        )
        logging.debug("已插入数据")

    def _background_rebuild_index(self, vault: str) -> None:
        """
        重建全文搜索索引
        """
        self.conn.execute(f"PRAGMA create_fts_index({vault}, id, content_fts, overwrite = 1)")

    def check_source(self, source: str, vault: str) -> bool:
        """
        检查特定来源的数据是否存在
        """
        if not self.check_vault(vault):
            return False
        result = self.conn.execute(f"SELECT EXISTS(SELECT 1 FROM {vault} WHERE source=?)", (source,)).fetchone()
        assert result is not None
        return result[0] == 1

    def _background_del_source(self, source: str, vault: str) -> None:
        """
        删除特定来源的数据
        """
        if not self.check_vault(vault):
            raise Exception("No such vault")
        self.conn.execute(f"DELETE FROM {vault} WHERE source=?", (source,))

    def _background_search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        """
        使用全文搜索查询
        :param query: 查询词
        :param vault: 存储库名称
        :param top_n: 返回结果数量
        """
        self.conn.execute(
            f"SELECT id, content FROM (SELECT *, fts_main_{vault}.match_bm25(id, ?) AS score FROM {vault}) WHERE score IS NOT NULL ORDER BY score DESC LIMIT ?",
            (" ".join(self.segment(query)), top_n),
        )
        return self.conn.fetchall()

    def _background_search_vec(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        """
        使用向量搜索查询
        :param query: 查询词
        :param vault: 存储库名称
        :param top_n: 返回结果数量
        """
        self.conn.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault} ORDER BY array_distance(content_vec, embedding(?)::FLOAT[{self.dims}]) LIMIT ?",
            (query, top_n),
        )
        return self.conn.fetchall()
