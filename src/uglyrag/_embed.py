from typing import List

from fastembed import TextEmbedding

# from fastembed.rerank.cross_encoder import TextCrossEncoder
# from uglyrag._integrations import JinaAPI
from uglyrag._config import config

model = TextEmbedding(
    model_name=config.get("embedding_model", "EMBEDDING", "BAAI/bge-small-zh-v1.5"),
    cache_dir=config.data_dir / "models",
)

"""
reranker = TextCrossEncoder(
    model_name=config.get("rerank_model", "EMBEDDING", "Xenova/ms-marco-MiniLM-L-6-v2"),
    cache_dir=config.data_dir / "models",
)
"""


class Embedder:
    """Embedder class for embedding text."""

    # dims = 1024
    dims = len(next(model.query_embed("hello")))

    @classmethod
    def embeddings(cls, docs: List[str]) -> List[List[float]]:
        return list(model.query_embed(docs))
        # return JinaAPI.embeddings(docs)

    @classmethod
    def embedding(cls, doc: str) -> List[float]:
        return cls.embeddings([doc])[0]


"""
    @classmethod
    def text_cross_enncoder(cls, query: str, documents: List[str]) -> List[float]:
        return list(reranker.rerank(query, documents))
"""
