from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Database(ABC):
    """
    定义数据库操作的抽象基类，包括分词和向量嵌入功能
    """

    segment: Callable[[str], list[str]]
    embedding: Callable[[str], list[float]]
    dims: int = 0
    executor: ThreadPoolExecutor = field(default_factory=lambda: ThreadPoolExecutor(max_workers=1))  # 使用单线程池

    def __post_init__(self) -> None:
        self.dims = len(self.embedding("Hello"))

    @abstractmethod
    def check_vault(self, vault: str) -> bool:
        """
        检查数据库是否存在，不存在则创建
        """
        pass

    @abstractmethod
    def _background_insert(self, data: tuple[str, str, str], vault: str) -> None:
        """
        插入数据
        """
        pass

    def _background_rebuild_index(self, vault: str) -> None:
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
    def _background_del_source(self, source: str, vault: str) -> None:
        """
        删除特定来源的数据
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

    async def run_in_executor(self, func: Callable, *args: Any) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    async def insert_data(self, data: tuple[str, str, str], vault: str) -> None:
        await self.run_in_executor(self._background_insert, data, vault)

    async def search(self, query: str, vault: str, top_n: int = 5) -> list[list[tuple[str, str]]]:
        result = await asyncio.gather(
            self.run_in_executor(self._background_search_fts, query, vault, top_n),
            self.run_in_executor(self._background_search_vec, query, vault, top_n),
        )
        return list(result)

    async def rebuild_index(self, vault: str) -> None:
        await self.run_in_executor(self._background_rebuild_index, vault)

    async def del_source(self, source: str, vault: str) -> None:
        await self.run_in_executor(self._background_del_source, source, vault)
