from dataclasses import dataclass, field
from typing import List, Optional, Set

import jieba_fast as jieba

from .base import BaseTokenizer
from .stop_words import stop_words


@dataclass
class Jieba(BaseTokenizer):
    stopwords: Optional[Set[str]] = field(default_factory=lambda: set(stop_words))

    def __call__(self, text: str) -> List[str]:
        words = jieba.cut_for_search(text)
        if self.stopwords:
            words = [w for w in words if w not in self.stopwords and w.strip()]
        return words
