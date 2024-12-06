import logging
from typing import Callable, List

from uglyrag._config import config

_embedding_module = config.get("embedding", "MODULES", "FastEmbed")
embedding: Callable[[str], List[float]] = None
if _embedding_module == "JINA":
    from uglyrag._integrations.jina import JinaAPI

    def embedding(x):
        return JinaAPI.embeddings([x])[0]

    logging.debug(f"使用 embedding 模块 {_embedding_module}")
elif _embedding_module == "FastEmbed":
    from uglyrag._integrations.fastembed import embedding

    embedding = embedding
    logging.debug(f"使用 embedding 模块 {_embedding_module}")
elif _embedding_module is None:
    raise ImportError("未配置 embedding 模块")
else:
    raise ImportError(f"No such embedding module: {_embedding_module}")

__all__ = ["embedding"]
