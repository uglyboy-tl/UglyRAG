import string
from dataclasses import dataclass, field
from typing import List, Optional, Set

import jieba_fast.posseg as pseg

from .base import BaseTokenizer
from .stop_words import stop_words

allow_speech_tags = {
    "an",
    "i",
    "j",
    "l",
    "n",
    "nr",
    "nrfg",
    "ns",
    "nt",
    "nz",
    "t",
    "v",
    "vd",
    "vn",
    "eng",
}


@dataclass
class Jieba(BaseTokenizer):
    stopwords: Optional[Set[str]] = field(default_factory=lambda: set(stop_words))

    def __call__(self, text: str) -> List[str]:
        # 结巴分词
        jieba_result = pseg.cut(text)
        # 词性筛选
        jieba_result = [w for w in jieba_result if w.flag in allow_speech_tags]
        # 去除特殊符号
        words = [w.word.strip() for w in jieba_result if w.flag != "x"]
        # 去除停用词
        words = [word for word in words if word not in stop_words and word not in string.punctuation and len(word) > 1]
        # 英文
        words = [word.lower() for word in words]

        return words
