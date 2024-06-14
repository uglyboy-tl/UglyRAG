from .base import BaseDocument
from .default import DefaultDocument
from .file import FileDocument


def get_document_class(name: str) -> BaseDocument:
    # 获取所有当前模块中的类
    subclasses = BaseDocument.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass
    return None


__all__ = [
    "BaseDocument",
    "DefaultDocument",
    "FileDocument",
    "get_document_class",
]
