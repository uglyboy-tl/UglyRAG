from .base import BaseTokenizer
from .jieba import Jieba


def get_tokenizer(name: str = "jieba") -> BaseTokenizer:
    if name == "jieba":
        return Jieba()
    else:
        raise ValueError(f"Tokenizer {name} not found")


__all__ = [
    "BaseTokenizer",
    "Jieba",
    "get_tokenizer",
]
