from typing import List, Tuple

from uglyrag._config import config
from uglyrag._index import Store

weight_fts = int(config.get("weight_fts", "RRF", 1))
weight_vec = int(config.get("weight_vec", "RRF", 1))
rrf_k = int(config.get("k", "RRF", 60))


def reciprocal_rank_fusion(fts_results, vec_results) -> List[Tuple[str, str]]:
    rank_dict = {}

    # Process FTS results
    for rank, (id, _) in enumerate(fts_results):
        if id not in rank_dict:
            rank_dict[id] = 0
        rank_dict[id] += 1 / (rrf_k + rank + 1) * weight_fts

    # Process vector results
    for rank, (id, _) in enumerate(vec_results):
        if id not in rank_dict:
            rank_dict[id] = 0
        rank_dict[id] += 1 / (rrf_k + rank + 1) * weight_vec

    # Sort by RRF score
    sorted_results = sorted(rank_dict.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def hybrid_search(query: str, vault="Core", top_n: int = 5) -> List[Tuple[str, str]]:
    store = Store.get()
    if not store.check_table(vault):
        raise Exception("No such vault")

    fts_results = store.search_fts(query, vault, top_n)
    vec_results = store.search_vec(query, vault, top_n)
    result_dict = dict(combine([fts_results, vec_results]))
    score_result = reciprocal_rank_fusion(fts_results, vec_results)
    return [(i, result_dict[i]) for i in [i[0] for i in score_result]][:top_n]


def combine(results: List[List[Tuple[str, str]]]) -> List[Tuple[str, str]]:
    results_dict = dict(results[0])
    for item in results[1:]:
        results_dict.update(dict(item))
    return list(results_dict.items())


def rerank(query: str, results: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    if not results:
        return []
    # scores = Embedder.text_cross_enncoder(query, [i[1] for i in results])
    scores = range(len(results), 0, -1)
    sorted_results = sorted(zip(results, scores, strict=False), key=lambda x: x[1], reverse=True)
    return [i[0] for i in sorted_results]


def search(query: str, vault="Core", top_n: int = 5) -> List[Tuple[str, str]]:
    results = combine([hybrid_search(query, vault, top_n)])
    # results = combine([store.search_fts(query, vault, top_n), store.search_vec(query, vault, top_n)])
    return rerank(query, results)[:top_n]
