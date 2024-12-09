from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

from uglyrag._config import config

model = TextEmbedding(
    model_name=config.get("embedding_model", "FastEmbed", "BAAI/bge-small-zh-v1.5"),
    cache_dir=config.data_dir / "models",
)


def embeddings(docs: list[str]) -> list[list[float]]:
    return list(model.query_embed(docs))


def embedding(doc: str) -> list[float]:
    return embeddings([doc])[0]


rerank_model = config.get("rerank_model", "FastEmbed")  # "Xenova/ms-marco-MiniLM-L-6-v2"
if rerank_model is not None:
    reranker = TextCrossEncoder(
        model_name=rerank_model,
        cache_dir=config.data_dir / "models",
    )
else:
    reranker = None


def rerank(query: str, documents: list[str]) -> list[float]:
    if reranker:
        return list(reranker.rerank(query, documents))
    else:
        raise NotImplementedError("No reranker model is specified.")
