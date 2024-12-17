from __future__ import annotations

from collections.abc import Callable

from uglyrag.config import config


def get_rerank_module() -> Callable[[str, list[str]], list[float]] | None:
    _rerank_module = config.get("rerank", "MODULES")
    rerank: Callable[[str, list[str]], list[float]] | None = None
    if not _rerank_module:
        raise ImportError("未配置 rerank 模块")
    elif _rerank_module == "JINA":
        from uglyrag.integrations.jina import JinaAPI

        rerank = JinaAPI.rerank
    elif _rerank_module == "FastEmbed":
        from uglyrag.integrations.fastembed import rerank
    else:
        raise ImportError(f"No such rerank module: {_rerank_module}")
    return rerank


rerank = get_rerank_module()

__all__ = ["rerank"]
