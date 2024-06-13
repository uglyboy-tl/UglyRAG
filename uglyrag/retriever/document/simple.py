from dataclasses import dataclass
from typing import List

from .base import BaseDocument
from .text_splitter import text_splitter


@dataclass
class SimpleDocument(BaseDocument):
    @property
    def indexed_contents(self) -> List[str]:
        return self.original_contents

    @property
    def original_contents(self) -> List[str]:
        if not hasattr(self, "_original_contents"):
            self._original_contents = text_splitter.split_text(self.doc)
        assert isinstance(self._original_contents, list)
        return self._original_contents
