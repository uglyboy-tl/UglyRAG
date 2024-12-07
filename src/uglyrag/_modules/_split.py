from typing import Callable, List, Tuple

from uglyrag._config import config

_split_module = config.get("split", "MODULES")
split: Callable[[str], List[Tuple[str, str]]] = None

if _split_module == "REGEX":
    from uglyrag._integrations.regex_chunk import split_text

    def split(text: str) -> List[Tuple[str, str]]:
        return [(str(i + 1), content) for i, content in enumerate(split_text(text))]
elif _split_module is None:
    raise ImportError("未配置 split 模块")
else:
    raise ImportError(f"No such rerank module: {_split_module}")

__all__ = ["split"]
