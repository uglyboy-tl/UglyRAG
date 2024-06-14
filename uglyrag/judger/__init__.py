from .base import Judger
from .llm_judger import LLMJudger
from .skr import SKRJudger


def get_judger(name: str) -> Judger:
    # 获取所有当前模块中的类
    subclasses = Judger.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass()
    return None


__all__ = ["Judger", "get_judger"]
