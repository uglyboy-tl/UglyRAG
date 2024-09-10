from dataclasses import dataclass, field
from typing import List

from .base import BaseDocument


@dataclass
class WebPageDocument(BaseDocument):
    path: str = field(init=False)
    _name_ = "WebPage"

    @property
    def indexed_contents(self) -> List[str]:
        return [self.path + "\n\n" + content for content in self.original_contents]
