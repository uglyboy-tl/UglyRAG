from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class BaseDocument(ABC):
    doc: str

    @property
    @abstractmethod
    def indexed_contents(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def original_contents(self) -> List[str]:
        pass
