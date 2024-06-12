from dataclasses import dataclass
from typing import List

from .base import BaseDocument


@dataclass
class SimpleDocument(BaseDocument):
    @property
    def indexed_contents(self) -> List[str]:
        return [self.doc]

    @property
    def original_contents(self) -> List[str]:
        return [self.doc]
