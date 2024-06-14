from abc import ABC, abstractmethod
from typing import Optional


class Judger(ABC):
    _name_ = ""

    @abstractmethod
    def __call__(self, query: str) -> Optional[str]:
        pass
