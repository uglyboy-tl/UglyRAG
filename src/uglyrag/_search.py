import logging
from typing import Callable, Dict, Generator, List, Tuple

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
    split: Callable[[str], List[Tuple[str, str]]] = lambda x: [("1", x)]
    default_vault: str = "Core"
    _db_instance = None
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
        if SearchEngine._db_instance is None:
            SearchEngine._db_instance = SQLiteStore(SearchEngine.segment, SearchEngine.embedding)
        return SearchEngine._db_instance

    @classmethod
    def build(cls, docs: List[Tuple[str, str]], vault: str = None, update_existing: bool = False):
        if not docs:
            return  # 如果 docs 为空，直接返回
        if vault is None:
            vault = cls.default_vault
        datas: List[Tuple[str, str, str]] = []
        for source, text in docs:
            if not source or not text:
                continue  # 跳过空字符串
            if cls._check_source(source, vault):  # 检查是否已经存在
                if not update_existing:  # 如果已经存在，且不允许更新，则跳过
                    continue
                cls.rm_source(source, vault)  # 如果已经存在，则删除, 并重建索引
            try:
                source_chunks: Generator[Tuple[str, str, str], None, None] = (
                    (source, pard_id, content) for pard_id, content in cls.split(text)
                )
                datas.extend(source_chunks)
            except Exception as e:
                logging.error(f"分割文档失败: {e}")
                continue  # 继续处理下一个文档
        cls._add(datas, vault)

    @classmethod
    def _add(cls, datas: List[Tuple[str, str, str]], vault: str):
        assert isinstance(datas, list)
        request_docs = []
        for data in datas:
            if isinstance(data, tuple) and len(data) == 3:
                _, _, content = data
            else:
                raise Exception("Invalid document format")
            if content not in cls._embeddings_dict:
                request_docs.append(content)
        embeddings = cls.embeddings(request_docs)
        for doc, i in zip(request_docs, embeddings, strict=False):
            cls._embeddings_dict[doc] = i

        store = cls.get()
        if not store.check_table(vault):
            return

        logging.info("构建索引...")
        for data in datas:
            if isinstance(data, tuple) and len(data) == 3:
                source, part_id, content = data
            else:
                raise Exception("Invalid document format")
            store.insert_row((source, part_id, content), vault)

    @classmethod
    def _check_source(cls, source: str, vault: str) -> bool:
        return cls.get().check_source(source, vault)

    @classmethod
    def rm_source(cls, source: str, vault: str = None):
        if vault is None:
            vault = cls.default_vault
        cls.get().rm_source(source, vault)

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
    def _hybrid_search(cls, query: str, vault: str, top_n: int = 5) -> List[Tuple[str, str]]:
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
    def search(cls, query: str, vault: str = None, top_n: int = 5) -> List[Tuple[str, str]]:
        if vault is None:
            vault = cls.default_vault
        if cls.rerank is None:
            logging.warning("使用混合搜索返回结果")
            return combine([cls._hybrid_search(query, vault, top_n)])
        else:
            store = cls.get()
            results = combine([store.search_fts(query, vault, top_n), store.search_vec(query, vault, top_n)])
            return cls._rerank(query, results)[:top_n]
