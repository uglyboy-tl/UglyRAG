from .base import BaseReranker
from .bge import BGE_Reranker


def get_reranker(name: str) -> BaseReranker:
    # 获取所有当前模块中的类
    subclasses = BaseReranker.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass()
    return None


__all__ = ["BaseReranker", "get_reranker"]
