from typing import List

from fastembed import TextEmbedding

# from uglyrag._integrations import JinaAPI

model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5", cache_dir="models")


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
