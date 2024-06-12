from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Type

from loguru import logger

from .document import BaseDocument, SimpleDocument


@dataclass
class Retriever(ABC):
    topk: int = 5

    def index(self, docs: List[str], cls: Type[BaseDocument] = SimpleDocument):
        logger.info(f"正在构建索引({self.__class__.__name__})...")
        indexed_contents = []
        original_contents = []
        for doc in docs:
            document = cls(doc)
            indexed_contents.extend(document.indexed_contents)
            original_contents.extend(document.original_contents)
        self._index(indexed_contents, original_contents)
        logger.success("索引构建完成")

    @abstractmethod
    def _index(self, indexes: List[str], contents: List[str]):
        pass

    @abstractmethod
    def search(self, query: str) -> List[str]:
        pass
