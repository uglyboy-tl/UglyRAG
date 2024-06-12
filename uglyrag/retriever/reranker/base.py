from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Reranker(ABC):
    def __call__(self, query: str, contexts: List[str]) -> Tuple[List[str], List[float]]:
        all_scores = self.get_rerank_scores(query, contexts)
        assert len(all_scores) == len(contexts)

        # sort contexts by score
        final_docs, final_scores = zip(
            *sorted(zip(contexts, all_scores, strict=False), key=lambda x: x[1], reverse=True), strict=False
        )

        return final_docs, final_scores

    @abstractmethod
    def get_rerank_scores(self, query: str, contexts: List[str]) -> List[float]:
        """
        计算给定查询和上下文文本列表的重新排名分数。

        这个方法目前尚未实现具体的分数计算逻辑，因此返回一个空列表。
        未来会根据具体的算法实现对每个上下文文本的排名分数计算。

        参数:
        query (str): 用户查询字符串。
        contexts (List[str]): 与查询相关的上下文文本列表。

        返回:
        List[float]: 上下文文本的重新排名分数列表，目前为空。
        """
        all_scores = []
        return all_scores
