from __future__ import annotations

from collections.abc import Callable

from uglyrag._config import config

_segment_module = config.get("segment", "MODULES")
segment: Callable[[str], list[str]] | None = None
if _segment_module == "Jieba":
    from uglyrag._integrations.jieba import segment
elif _segment_module is None:
    raise ImportError("未配置 segment 模块")
else:
    raise ImportError(f"No such segment module: {_segment_module}")

__all__ = ["segment"]
