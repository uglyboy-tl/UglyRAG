from typing import List

from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

# from uglyrag._integrations import JinaAPI
from uglyrag._config import config

model = TextEmbedding(
    model_name=config.get("embedding_model", "EMBEDDING", "BAAI/bge-small-zh-v1.5"),
    cache_dir=config.data_dir / "models",
)


def embeddings(docs: List[str]) -> List[List[float]]:
    # return JinaAPI.embeddings(docs)
    return list(model.query_embed(docs))


def embedding(doc: str) -> List[float]:
    return embeddings([doc])[0]


"""
reranker = TextCrossEncoder(
    model_name=config.get("rerank_model", "EMBEDDING", "Xenova/ms-marco-MiniLM-L-6-v2"),
    cache_dir=config.data_dir / "models",
)


def text_cross_enncoder(query: str, documents: List[str]) -> List[float]:
    return list(reranker.rerank(query, documents))
"""
