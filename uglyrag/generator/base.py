from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Generator(ABC):
    @abstractmethod
    def __call__(self, query: str, retrieval_results: Optional[List[str]] = None) -> str:
        pass
