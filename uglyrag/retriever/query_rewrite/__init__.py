from .base import BaseQueryRewrite
from .default import DefaultQueryRewrite
from .hyde import HyDEQueryRewrite
from .step_back_prompting import StepBackPromptingQueryRewrite
from .sub_question import SubQuestionQueryRewrite


def get_query_rewrite(name: str) -> BaseQueryRewrite:
    # 获取所有当前模块中的类
    subclasses = BaseQueryRewrite.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass()
    return None


__all__ = [
    "BaseQueryRewrite",
    "DefaultQueryRewrite",
    "SubQuestionQueryRewrite",
    "StepBackPromptingQueryRewrite",
    "HyDEQueryRewrite",
    "get_query_rewrite",
]
