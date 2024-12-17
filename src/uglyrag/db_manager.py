from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from threading import Lock
from typing import Any

from uglyrag.config import config
from uglyrag.database import Database
from uglyrag.database._sqlite import SQLiteDatebase


class DatabaseManager:
    segment: Callable[[str], list[str]] = staticmethod(lambda x: [x])
    embeddings: Callable[[list[str]], list[list[float]]] = staticmethod(lambda x: [[1.0] * len(x)])
    _executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)  # 使用多线程池
    _embeddings_dict: defaultdict[str, list[float]] = defaultdict(list)
    _check_vault_dict: defaultdict[str, bool] = defaultdict(bool)
    _lock = Lock()

    @staticmethod
    @cache
    def get_database() -> Database:
        """获取数据库实例"""
        db_filename = config.get("db_name")
        db_path = config.data_dir / db_filename
        db_type = config.get("db_type").lower()
        db_classes: dict[str, type[Database] | None] = {
            "sqlite": SQLiteDatebase,
            "duckdb": None,  # DuckDBDatabase will be imported later
        }
        db_class: type[Database] | None = db_classes.get(db_type)
        if db_class is None:
            if db_type == "duckdb":
                try:
                    from uglyrag.database._duckdb import DuckDBDatabase

                    db_class = DuckDBDatabase
                except ImportError as e:
                    raise ImportError("DuckDB 未安装，请先安装 DuckDB") from e
            else:
                logging.error(f"不支持的数据库类型: {db_type}")
                raise ValueError(f"不支持的数据库类型: {db_type}")
        logging.debug(f"使用 {db_type.upper()} 数据库")
        return db_class(db_path, DatabaseManager.segment, DatabaseManager._get_embedding)

    @classmethod
    def reset(cls) -> None:
        cls.get_database().reset()

    @classmethod
    def search(cls, query: str, vault: str, top_n: int = 5) -> list[list[tuple[str, str]]]:
        return asyncio.run(cls._async_search(query, vault, top_n))

    @classmethod
    def add_documents(cls, data: list[tuple[str, str, str]], vault: str) -> None:
        """添加文档到数据库"""
        if not data:
            return
        if not cls._is_vault_valid(vault):
            raise Exception("No such vault")

        request_docs = [content for _, _, content in data if content not in cls._embeddings_dict]
        embeddings = cls.embeddings(request_docs)
        with cls._lock:
            cls._embeddings_dict.update(zip(request_docs, embeddings))

        with cls.get_database() as store:
            logging.info("构建索引...")
            store.insert_data(data, vault)
            store.rebuild_index(vault)

    @classmethod
    def is_source_valid(cls, source: str, vault: str, rm_if_exist: bool = False) -> bool:
        """检查源的有效性"""
        if not cls._is_vault_valid(vault):
            raise Exception("No such vault")
        store = cls.get_database()
        if not store.check_source(source, vault):
            return False
        return not rm_if_exist or store.del_source(source, vault)

    @classmethod
    def _get_embedding(cls, text: str) -> list[float]:
        """获取文本的嵌入向量"""
        if text in cls._embeddings_dict:
            return cls._embeddings_dict[text]
        embedding = cls.embeddings([text])[0]
        with cls._lock:
            cls._embeddings_dict[text] = embedding
        return embedding

    @classmethod
    def _is_vault_valid(cls, vault: str) -> bool:
        with cls.get_database() as store:
            if vault in cls._check_vault_dict:
                return cls._check_vault_dict[vault]
            else:
                try:
                    result = store._check_vault(vault)
                    with cls._lock:
                        cls._check_vault_dict[vault] = result
                    return result
                except Exception as e:
                    # 处理异常，可以根据具体需求进行日志记录或其他操作
                    logging.error(f"Error checking vault: {e}")
                    return False

    @classmethod
    async def _run_in_executor(cls, func: Callable, *args: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(cls._executor, func, *args)
            return result
        except RuntimeError as e:
            # 处理事件循环获取失败的情况
            logging.error(f"Failed to get the running event loop: {e}")
            raise
        except Exception as e:
            # 处理 func 调用过程中可能抛出的异常
            logging.error(f"An error occurred while executing the function: {e}")
            raise

    @classmethod
    async def _async_search(cls, query: str, vault: str, top_n: int = 5) -> list[list[tuple[str, str]]]:
        if not cls._is_vault_valid(vault):
            raise Exception("No such vault")
        store = cls.get_database()
        result = await asyncio.gather(
            cls._run_in_executor(store._background_search_fts, query, vault, top_n),
            cls._run_in_executor(store._background_search_vec, query, vault, top_n),
        )
        return list(result)
