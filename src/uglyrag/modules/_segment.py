from __future__ import annotations

from collections.abc import Callable

from uglyrag.config import config


def get_segment_module() -> Callable[[str], list[str]] | None:
    _segment_module = config.get("segment", "MODULES")
    segment: Callable[[str], list[str]] | None = None
    if not _segment_module:
        raise ImportError("未配置 segment 模块")
    elif _segment_module == "Jieba":
        from uglyrag.integrations.jieba import segment
    else:
        raise ImportError(f"No such segment module: {_segment_module}")
    return segment


segment = get_segment_module()

__all__ = ["segment"]
