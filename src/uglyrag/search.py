from __future__ import annotations

import logging
from collections.abc import Callable
from functools import cache
from typing import Any

from uglyrag._database import Database, factory_db
from uglyrag.config import config


def merge_results(results: list[list[tuple[str, str]]]) -> dict[str, str]:
    """合并搜索结果，搜索结果的结构是 List[(id, content)]"""
    results_dict = dict(results[0])
    for item in results[1:]:
        results_dict.update(dict(item))
    return results_dict


class SearchEngine:
    segment: Callable[[str], list[str]] = lambda x: [x]
    embeddings: Callable[[list[str]], list[list[float]]] = lambda x: [[1] * len(x)]
    rerank: Callable[[str, list[str]], list[float]] | None = None
    split: Callable[[str], list[tuple[str, str]]] = lambda x: [("1", x)]
    default_vault: str = "Core"
    _embeddings_dict: dict[str, list[float]] = {}

    _weight_fts: float = float(config.get("weight_fts", "RRF", "1.0"))
    _weight_vec: float = float(config.get("weight_vec", "RRF", "1.0"))
    _rrf_k: int = int(config.get("k", "RRF", "60"))

    @classmethod
    def get_embedding(cls, text: str) -> list[float]:
        """获取文本的嵌入向量"""
        if text in cls._embeddings_dict:
            return cls._embeddings_dict[text]
        return cls.embeddings([text])[0]

    @staticmethod
    @cache
    def get_database() -> Database:
        """获取数据库实例"""
        return factory_db(SearchEngine.segment, SearchEngine.get_embedding)

    @classmethod
    def build_index(
        cls,
        docs: list[tuple[Any, str]],
        vault: str | None = None,
        reset_db: bool = False,
        update_exist: bool = False,
    ) -> None:
        """构建索引"""
        if reset_db:
            cls.get_database().reset()
        if not docs:
            return  # 如果 docs 为空，直接返回
        if vault is None:
            vault = cls.default_vault
        data: list[tuple[str, str, str]] = []
        for source, text in docs:
            source = str(source)
            if not source or not text:
                continue  # 跳过空字符串
            if (
                cls._is_source_valid(source, vault, rm_if_exist=update_exist) and not update_exist
            ):  # 如果已经存在，且不允许更新，则跳过
                continue
            try:
                data.extend((source, pard_id, content) for pard_id, content in cls.split(text))
            except Exception as e:
                logging.error(f"分割文档失败: {e}")
                continue  # 继续处理下一个文档
        cls._add_documents(data, vault)

    @classmethod
    def _add_documents(cls, data: list[tuple[str, str, str]], vault: str) -> None:
        """添加文档到数据库"""
        if not data:
            return

        request_docs = [content for _, _, content in data if content not in cls._embeddings_dict]
        embeddings = cls.embeddings(request_docs)
        for doc, i in zip(request_docs, embeddings):
            cls._embeddings_dict[doc] = i

        with cls.get_database() as store:
            logging.info("构建索引...")
            store.insert_data(data, vault)
            store.rebuild_index(vault)

    @classmethod
    def _is_source_valid(cls, source: str, vault: str | None = None, rm_if_exist: bool = False) -> bool:
        if vault is None:
            vault = cls.default_vault
        """检查源的有效性"""
        if not cls.get_database().check_source(source, vault):
            return False
        return not rm_if_exist or cls.get_database().del_source(source, vault)

    @classmethod
    def _calculate_rrf(
        cls, fts_results: list[tuple[str, str]], vec_results: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        result_dict = merge_results([fts_results, vec_results])
        rank_dict = {}

        # Process FTS results
        for rank, (id, _) in enumerate(fts_results):
            if id not in rank_dict:
                rank_dict[id] = 0.0
            rank_dict[id] += 1 / (cls._rrf_k + rank + 1) * cls._weight_fts

        # Process vector results
        for rank, (id, _) in enumerate(vec_results):
            if id not in rank_dict:
                rank_dict[id] = 0.0
            rank_dict[id] += 1 / (cls._rrf_k + rank + 1) * cls._weight_vec

        # Sort by RRF score
        sorted_results = sorted(rank_dict.items(), key=lambda x: x[1], reverse=True)
        return [(i, result_dict[i]) for i, _ in sorted_results]

    @classmethod
    def _rerank(cls, query: str, results: dict[str, str]) -> list[tuple[str, str]]:
        if not results or cls.rerank is None:
            return []
        scores = cls.rerank(query, [content for _, content in results.items()])
        sorted_results = sorted(
            ((key, value, score) for (key, value), score in zip(results.items(), scores)),
            key=lambda x: x[2],
            reverse=True,
        )
        return [(key, value) for key, value, _ in sorted_results]

    @classmethod
    def search(cls, query: str, vault: str | None = None, top_n: int = 5) -> list[tuple[str, str]]:
        if vault is None:
            vault = cls.default_vault
        with cls.get_database() as store:
            if not store.check_vault(vault):
                raise Exception("No such vault")
            results = store.search(query, vault, top_n)
            if cls.rerank is None:
                logging.warning("使用混合搜索返回结果")
                fts_results, vec_results = results[:2]
                return cls._calculate_rrf(fts_results, vec_results)[:top_n]
            else:
                return cls._rerank(query, merge_results(results))[:top_n]
