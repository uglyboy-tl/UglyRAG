from __future__ import annotations

from collections.abc import Callable

from uglyrag.config import config


def get_split_module() -> Callable[[str], list[tuple[str, str]]] | None:
    _split_module = config.get("split", "MODULES")
    split: Callable[[str], list[tuple[str, str]]] | None = None

    if not _split_module:
        raise ImportError("未配置 split 模块")
    elif _split_module == "REGEX":
        from uglyrag.integrations.regex_chunk import split_text

        def split_func(x: str) -> list[tuple[str, str]]:
            return [(str(i + 1), content) for i, content in enumerate(split_text(x))]

        split = split_func
    else:
        raise ImportError(f"No such split module: {_split_module}")
    return split
