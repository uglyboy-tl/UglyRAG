from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseQueryRewrite(ABC):
    _name_ = ""

    @abstractmethod
    def __call__(self, query: str) -> str:
        pass
