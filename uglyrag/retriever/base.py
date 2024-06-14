from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from .document import get_document_class
from .query_rewrite import BaseQueryRewrite, get_query_rewrite
from .reranker import BaseReranker, get_reranker

K = 4


@dataclass
class Retriever(ABC):
    _name_ = ""
    topk: int = 5
    config: Dict[str, str] = field(default_factory=dict)
    init_needed: bool = False

    query_rewrite: Optional[BaseQueryRewrite] = field(init=False)
    reranker: Optional[BaseReranker] = field(init=False)

    def __post_init__(self) -> None:
        self.query_rewrite = get_query_rewrite(self.config.get("query_rewrite", "Default"))
        self.reranker = get_reranker(self.config.get("reranker", "Default"))

    def index(self, docs: List[str], docs_type: str = "Default"):
        logger.info(f"正在构建索引({self.__class__.__name__})...")
        indexed_contents = []
        original_contents = []
        for doc in docs:
            document = get_document_class(docs_type)(doc)
            indexed_contents.extend(document.indexed_contents)
            original_contents.extend(document.original_contents)
        self._index(indexed_contents, original_contents)
        logger.success("索引构建完成")

    def search(self, query: str) -> List[str]:
        if self.query_rewrite:
            logger.info("正在重写查询...")
            query = self.query_rewrite(query)
        contexts = self._search(query, self.topk * K if self.reranker else self.topk)
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
