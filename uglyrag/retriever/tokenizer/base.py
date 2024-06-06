from abc import ABC, abstractmethod
from typing import List


class BaseTokenizer(ABC):
    @abstractmethod
    def __call__(self, text: str) -> List[str]:
        pass
