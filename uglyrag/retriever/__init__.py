from typing import Type

from .base import Retriever
from .chroma import Chroma
from .sqlite import SQLite


def get_retriever_class(name: str) -> Type[Retriever]:
    # 获取所有当前模块中的类
    subclasses = Retriever.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass
    return None


__all__ = [
    "Retriever",
    "Chroma",
    "SQLite",
    "get_retriever_class",
]
