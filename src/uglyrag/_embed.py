from typing import List

from fastembed import TextEmbedding


class Embedder:
    """Embedder class for embedding text."""

    model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    dims = len(next(model.query_embed("hello")))

    @classmethod
    def embedding(cls, doc: str) -> List[float]:
        return list(cls.model.query_embed(doc))[0]

    @classmethod
    def embeddings(cls, docs: List[str]) -> List[List[float]]:
        return list(cls.model.query_embed(docs))
