import logging
from typing import Callable, List

from uglyrag._config import config

_rerank_module = config.get("rerank", "MODULES")
rerank: Callable[[str, List[str]], List[float]] = None
if _rerank_module == "JINA":
    from uglyrag._integrations.jina import JinaAPI

    rerank = JinaAPI.rerank
    logging.debug(f"使用 rerank 模块 {_rerank_module}")
elif _rerank_module == "FastEmbed":
    from uglyrag._integrations.fastembed import text_cross_enncoder

    rerank = text_cross_enncoder
    logging.debug(f"使用 rerank 模块 {_rerank_module}")
elif _rerank_module is None:
    raise ImportError("未配置 rerank 模块")
else:
    raise ImportError(f"No such rerank module: {_rerank_module}")

__all__ = ["rerank"]
