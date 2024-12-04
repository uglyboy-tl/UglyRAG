from uglyrag._config import Config
from uglyrag._embed import Embedder
from uglyrag._sqlite import SQLiteStore
from uglyrag._tokenize import tokenize

config = Config()
store = SQLiteStore()

weight_fts = int(config.get("weight_fts", "RRF", 1))
weight_vec = int(config.get("weight_vec", "RRF", 1))
rrf_k = int(config.get("k", "RRF", 60))


def keyword_search(query: str, vault="Core", top_n: int = 5) -> list[tuple[str, str]]:
    store.cursor.execute(
        f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
        (" OR ".join(tokenize(query)), top_n),
    )
    return store.cursor.fetchall()


def vector_search(query: str, vault="Core", top_n: int = 5) -> list[tuple[str, str]]:
    store.cursor.execute(
        f"SELECT {vault}.id, {vault}.content FROM {vault}_vec join {vault} on {vault}_vec.rowid={vault}.id WHERE embedding MATCH ? AND k = ? ORDER BY distance;",
        (Embedder.embedding(query), top_n),
    )
    return store.cursor.fetchall()


def reciprocal_rank_fusion(fts_results, vec_results) -> list[tuple[str, str]]:
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


def hybrid_search(query: str, vault="Core", top_n: int = 5) -> list[tuple[str, str]]:
    if not store.check_table(vault):
        raise Exception("No such vault")

    fts_results = keyword_search(query, vault, top_n)
    vec_results = vector_search(query, vault, top_n)
    return reciprocal_rank_fusion(fts_results, vec_results)
