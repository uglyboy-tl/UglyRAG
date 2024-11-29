from ._config import Config
from ._embed import embedding
from ._sqlite import SQLiteStore
from ._tokenize import tokenize

config = Config()
store = SQLiteStore()

weight_fts = int(config.get("weight_fts", "RRF", 1))
weight_vec = int(config.get("weight_vec", "RRF", 1))
rrf_k = int(config.get("k", "RRF", 60))


def keyword_search(query: str, vault="Core", top_n: int = 5) -> tuple[list[str], list[float]]:
    store.cursor.execute(
        f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
        (" OR ".join(tokenize(query)), top_n),
    )
    return store.cursor.fetchall()


def vector_search(query: str, vault="Core", top_n: int = 5) -> tuple[list[str], list[float]]:
    store.cursor.excute(
        f"SELECT {vault}.id, {vault}.content FROM {vault}_vec join {vault} on {vault}_vec.rowid={vault}.id WHERE headline_embedding MATCH ? AND k = ? ORDER BY distance;",
        (embedding(query), top_n),
    )
    return store.cursor.fetchall()


def reciprocal_rank_fusion(fts_results, vec_results):
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


'''
def hybrid_search(query: str, *, num_results: int = 3, num_rerank: int = 100) -> tuple[list[str], list[float]]:
    """Search chunks by combining ANN vector search with BM25 keyword search."""
    # Run both searches.
    vs_chunk_ids, _ = vector_search(query, num_results=num_rerank)
    ks_chunk_ids, _ = keyword_search(query, num_results=num_rerank)
    # Combine the results with Reciprocal Rank Fusion (RRF).
    chunk_ids, hybrid_score = reciprocal_rank_fusion([vs_chunk_ids, ks_chunk_ids])
    chunk_ids, hybrid_score = chunk_ids[:num_results], hybrid_score[:num_results]
    return chunk_ids, hybrid_score
'''


def hybrid_search(query: str, vault="Core", top_n: int = 5):
    return keyword_search(query, vault, top_n)
