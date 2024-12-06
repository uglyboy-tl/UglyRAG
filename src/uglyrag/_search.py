import logging
from typing import Callable, Dict, List, Tuple

from uglyrag._config import config
from uglyrag._sqlite import SQLiteStore


# 合并搜索结果，搜索结果的结构是 List[(id, content)]
def combine(results: List[List[Tuple[str, str]]]) -> List[Tuple[str, str]]:
    results_dict = dict(results[0])
    for item in results[1:]:
        results_dict.update(dict(item))
    return list(results_dict.items())


class SearchEngine:
    segment: Callable[[str], List[str]] = lambda x: [x]
    embeddings: Callable[[List[str]], List[List[float]]] = lambda x: [[1] * len(x)]
    rerank: Callable[[str, List[str]], List[float]] = None
    _instance = None
    _embeddings_dict: Dict[str, List[float]] = {}

    _weight_fts: int = int(config.get("weight_fts", "RRF", 1))
    _weight_vec: int = int(config.get("weight_vec", "RRF", 1))
    _rrf_k: int = int(config.get("k", "RRF", 60))

    @classmethod
    def embedding(cls, text: str) -> List[float]:
        if text in cls._embeddings_dict:
            return cls._embeddings_dict[text]
        return cls.embeddings([text])[0]

    @staticmethod
    def get() -> SQLiteStore:
        if SearchEngine._instance is None:
            SearchEngine._instance = SQLiteStore(SearchEngine.segment, SearchEngine.embedding)
        return SearchEngine._instance

    @classmethod
    def build(cls, docs: List[Tuple[str, str, str]], vault: str = "Core"):
        request_docs = [doc for _, _, doc in docs]
        for text in docs:
            if text in cls._embeddings_dict:
                request_docs.pop(text)
        embeddings = cls.embeddings(request_docs)
        for doc, i in zip(request_docs, embeddings, strict=False):
            cls._embeddings_dict[doc] = i

        store = cls.get()
        if not store.check_table(vault):
            return

        logging.info("构建索引...")
        for title, partition, content in docs:
            store.insert_row((title, partition, content))

    @classmethod
    def _reciprocal_rank_fusion(cls, fts_results, vec_results) -> List[Tuple[str, str]]:
        rank_dict = {}

        # Process FTS results
        for rank, (id, _) in enumerate(fts_results):
            if id not in rank_dict:
                rank_dict[id] = 0
            rank_dict[id] += 1 / (cls._rrf_k + rank + 1) * cls._weight_fts

        # Process vector results
        for rank, (id, _) in enumerate(vec_results):
            if id not in rank_dict:
                rank_dict[id] = 0
            rank_dict[id] += 1 / (cls._rrf_k + rank + 1) * cls._weight_vec

        # Sort by RRF score
        sorted_results = sorted(rank_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_results

    @classmethod
    def hybrid_search(cls, query: str, vault="Core", top_n: int = 5) -> List[Tuple[str, str]]:
        store = SearchEngine.get()
        if not store.check_table(vault):
            raise Exception("No such vault")

        fts_results = store.search_fts(query, vault, top_n)
        vec_results = store.search_vec(query, vault, top_n)
        result_dict = dict(combine([fts_results, vec_results]))
        score_result = cls._reciprocal_rank_fusion(fts_results, vec_results)
        return [(i, result_dict[i]) for i in [i[0] for i in score_result]][:top_n]

    @classmethod
    def _rerank(cls, query: str, results: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        if not results:
            return []
        scores = cls.rerank(query, [i[1] for i in results])
        sorted_results = sorted(zip(results, scores, strict=False), key=lambda x: x[1], reverse=True)
        return [i[0] for i in sorted_results]

    @classmethod
    def search(cls, query: str, vault="Core", top_n: int = 5) -> List[Tuple[str, str]]:
        if cls.rerank is None:
            logging.warning("使用混合搜索返回结果")
            return combine([cls.hybrid_search(query, vault, top_n)])
        else:
            store = cls.get()
            results = combine([store.search_fts(query, vault, top_n), store.search_vec(query, vault, top_n)])
            return cls._rerank(query, results)[:top_n]
