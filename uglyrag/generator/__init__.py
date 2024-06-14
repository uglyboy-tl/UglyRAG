from typing import Type

from .base import LLM, Generator
from .openai import OpenAI_Generator


def get_generator_class(name: str) -> Type[Generator]:
    # 获取所有当前模块中的类
    subclasses = Generator.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass
    return None


__all__ = ["Generator", "LLM", "get_generator_class"]
