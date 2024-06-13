from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Type

from loguru import logger

from .document import BaseDocument, SimpleDocument
from .reranker import Reranker


@dataclass
class Retriever(ABC):
    topk: int = 5
    reranker: Optional[Reranker] = None

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

    def search(self, query: str) -> List[str]:
        contexts = self._search(query, self.topk * 4 if self.reranker else self.topk)
        if self.reranker:
            logger.info("正在重新排序...")
            contexts, scores = self.reranker(query, contexts)
            # 根据分数排序并取前topk个
            contexts = [
                contexts[i] for i in sorted(range(len(scores)), key=lambda k: scores[k], reverse=True)[: self.topk]
            ]
        return contexts

    @abstractmethod
    def _index(self, indexes: List[str], contents: List[str]):
        pass

    @abstractmethod
    def _search(self, query: str) -> List[str]:
        pass
