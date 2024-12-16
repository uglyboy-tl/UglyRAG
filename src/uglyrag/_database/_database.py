from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from types import TracebackType
from typing import Any


@dataclass
class Database(ABC):
    """
    定义数据库操作的抽象基类，包括分词和向量嵌入功能
    """

    db_path: Path
    segment: Callable[[str], list[str]]
    embedding: Callable[[str], list[float]]
    dims: int = field(init=False)
    executor: ThreadPoolExecutor = field(default_factory=lambda: ThreadPoolExecutor(max_workers=1))  # 使用单线程池
    DATABASE_FILE_EXTENSION: str = "db"
    _check_vault_dict: dict[str, bool] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        if not self.db_path.name.endswith(f".{self.DATABASE_FILE_EXTENSION}"):
            raise ValueError(f"无效的数据库文件路径，必须以 .{self.DATABASE_FILE_EXTENSION} 结尾")
        self.dims = len(self.embedding("Hello"))

    def __enter__(self) -> Database:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        return

    @abstractmethod
    def reset(self) -> None:
        """
        重置数据库
        """
        if self.db_path.exists():
            self.db_path.unlink()

    def rebuild_index(self, vault: str) -> None:
        """
        重建全文搜索索引
        """
        return

    @abstractmethod
    def check_source(self, source: str, vault: str) -> bool:
        """
        检查特定来源的数据是否存在
        """
        pass

    @abstractmethod
    def del_source(self, source: str, vault: str) -> bool:
        """
        删除特定来源的数据
        """
        pass

    def check_vault(self, vault: str) -> bool:
        if vault in self._check_vault_dict:
            return self._check_vault_dict[vault]
        else:
            try:
                result = self._check_vault(vault)
                self._check_vault_dict[vault] = result
                return result
            except Exception as e:
                # 处理异常，可以根据具体需求进行日志记录或其他操作
                logging.error(f"Error checking vault: {e}")
                return False

    @abstractmethod
    def insert_data(self, data: list[tuple[str, str, str]], vault: str) -> None:
        """
        插入数据
        """
        pass

    def search(self, query: str, vault: str, top_n: int = 5) -> list[list[tuple[str, str]]]:
        return asyncio.run(self._async_search(query, vault, top_n))

    @abstractmethod
    def _check_vault(self, vault: str) -> bool:
        """
        检查数据库是否存在，不存在则创建
        """
        pass

    @abstractmethod
    def _background_search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        """
        使用全文搜索查询
        :param query: 查询词
        :param vault: 存储库名称
        :param top_n: 返回结果数量
        """
        pass

    @abstractmethod
    def _background_search_vec(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        """
        使用向量搜索查询
        :param query: 查询词
        :param vault: 存储库名称
        :param top_n: 返回结果数量
        """
        pass

    async def _run_in_executor(self, func: Callable, *args: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(self.executor, func, *args)
            return result
        except RuntimeError as e:
            # 处理事件循环获取失败的情况
            logging.error(f"Failed to get the running event loop: {e}")
            raise
        except Exception as e:
            # 处理 func 调用过程中可能抛出的异常
            logging.error(f"An error occurred while executing the function: {e}")
            raise

    async def _async_search(self, query: str, vault: str, top_n: int = 5) -> list[list[tuple[str, str]]]:
        if not self.check_vault(vault):
            return []
        result = await asyncio.gather(
            self._run_in_executor(self._background_search_fts, query, vault, top_n),
            self._run_in_executor(self._background_search_vec, query, vault, top_n),
        )
        return list(result)
