from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class BaseReranker(ABC):
    _name_ = ""

    @abstractmethod
    def __call__(self, query: str, contexts: List[str], top_n: int) -> List[Tuple[str, float]]:
        pass
