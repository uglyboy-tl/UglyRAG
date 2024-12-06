from typing import Callable, List

from uglyrag._config import config

_embedding_module = config.get("embedding", "MODULES", "FastEmbed")
embedding: Callable[[str], List[float]] = None
if _embedding_module == "JINA":
    from uglyrag._integrations.jina import JinaAPI

    embedding = JinaAPI.embedding

elif _embedding_module == "FastEmbed":
    from uglyrag._integrations.fastembed import embedding
elif _embedding_module is None:
    raise ImportError("未配置 embedding 模块")
else:
    raise ImportError(f"No such embedding module: {_embedding_module}")

__all__ = ["embedding"]
