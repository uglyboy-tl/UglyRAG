from __future__ import annotations

from collections.abc import Callable

from uglyrag.config import config


def get_embeddings_module() -> Callable[[list[str]], list[list[float]]] | None:
    _embedding_module = config.get("embedding", "MODULES", "JINA")

    embeddings: Callable[[list[str]], list[list[float]]] | None = None
    if not _embedding_module:
        raise ImportError("未配置 embedding 模块")
    elif _embedding_module == "FastEmbed":
        from uglyrag.integrations.fastembed import embeddings
    elif _embedding_module == "JINA":
        from uglyrag.integrations.jina import JinaAPI

        embeddings = JinaAPI.embeddings
    else:
        print(f"get_embeddings_module: raising ImportError for {_embedding_module}")
        raise ImportError(f"No such embedding module: {_embedding_module}")
    return embeddings
