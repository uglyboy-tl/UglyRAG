from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Database(ABC):
    """
    定义数据库操作的抽象基类，包括分词和向量嵌入功能
    """

    segment: Callable[[str], list[str]]
    embedding: Callable[[str], list[float]]

    @abstractmethod
    def check_vault(self) -> bool:
        """
        检查数据库是否存在，不存在则创建
        """
        pass

    @abstractmethod
    def insert_data(self, data: tuple[str], vault: str):
        """
        插入数据
        """
        pass

    @abstractmethod
    def check_source(self, source: str, vault: str) -> bool:
        """
        检查特定来源的数据是否存在
        """
        pass

    @abstractmethod
    def rm_source(self, source: str, vault: str):
        """
        删除特定来源的数据
        """
        pass

    @abstractmethod
    def search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        """
        使用全文搜索查询
        :param query: 查询词
        :param vault: 存储库名称
        :param top_n: 返回结果数量
        """
        pass

    @abstractmethod
    def search_vec(self, query: list[float], vault: str, top_n: int = 5) -> list[tuple[str, float]]:
        """
        使用向量搜索查询
        :param query: 查询词
        :param vault: 存储库名称
        :param top_n: 返回结果数量
        """
        pass
