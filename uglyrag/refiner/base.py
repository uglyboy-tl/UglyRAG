from abc import ABC, abstractmethod
from typing import List


class ReFiner(ABC):
    @abstractmethod
    def __call__(self, query: str, contexts: List[str]) -> List[str]:
        pass
