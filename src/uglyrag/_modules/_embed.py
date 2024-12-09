from __future__ import annotations

from collections.abc import Callable

from uglyrag._config import config

_embedding_module = config.get("embedding", "MODULES", "JINA")
embeddings: Callable[[str], list[float]] = None
if _embedding_module == "JINA":
    from uglyrag._integrations.jina import JinaAPI

    embeddings = JinaAPI.embeddings

elif _embedding_module == "FastEmbed":
    from uglyrag._integrations.fastembed import embeddings
elif _embedding_module is None:
    raise ImportError("未配置 embedding 模块")
else:
    raise ImportError(f"No such embedding module: {_embedding_module}")

__all__ = ["embeddings"]
