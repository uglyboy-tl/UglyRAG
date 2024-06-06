from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class Retriever(ABC):
    @abstractmethod
    def index(self, docs: List[str]):
        pass

    @abstractmethod
    def search(self, query: str) -> List[str]:
        pass
