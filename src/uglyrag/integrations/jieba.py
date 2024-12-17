from __future__ import annotations

import logging
import string

import jieba_fast
import jieba_fast.posseg as pseg

from data.stop_words import stop_words

jieba_fast.setLogLevel(logging.INFO)
allow_speech_tags = {"an", "i", "j", "l", "n", "nr", "nrfg", "ns", "nt", "nz", "t", "v", "vd", "vn", "eng"}


def segment(text: str) -> list[str]:
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
