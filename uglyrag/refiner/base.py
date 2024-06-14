from abc import ABC, abstractmethod
from typing import List


class Refiner(ABC):
    _name_ = ""

    @abstractmethod
    def __call__(self, query: str, contexts: List[str]) -> List[str]:
        pass
