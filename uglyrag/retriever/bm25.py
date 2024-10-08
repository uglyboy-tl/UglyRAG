#!/usr/bin/env python3

import concurrent.futures
import heapq
import itertools
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

from .base import BaseRetriever
from .tokenizer import get_tokenizer

tokenizer = get_tokenizer()


@dataclass
class BM25:
    k1: float = 1.5
    b: float = 0.75
    preprocessed_texts: List[str] = field(default_factory=list)
    word_sets: List[Set[str]] = field(default_factory=list)
    text_lens: List[int] = field(default_factory=list)
    tf_values: dict = field(default_factory=dict)
    idf_values: dict = field(default_factory=dict)
    sum_len: float = field(default=0)

    def calculate_tf(self, word: str, text: str) -> float:
        return text.split().count(word) / len(text.split())

    def calculate_idf(self, word: str) -> float:
        matches = len([True for text in self.preprocessed_texts if word in text.split()])
        return math.log(len(self.preprocessed_texts) / matches) if matches else 0.0

    def calculate_bm25_score(self, i: int, query: str) -> float:
        score = 0
        preprocessed_query = tokenizer(query)
        for word in preprocessed_query:
            if word not in self.word_sets[i]:
                continue
            key = f"{word}_{i}"
            tf_value = self.tf_values.get(key, 1e-9)
            idf_value = self.idf_values.get(word, 0)
            tf_idf_value = tf_value * idf_value
            text_len = self.text_lens[i]
            avg_len = self.sum_len / len(self.preprocessed_texts) if self.preprocessed_texts else 1
            score_part = (self.k1 + 1) / (tf_value + self.k1 * (1 - self.b + self.b * text_len / avg_len))
            score += tf_idf_value * score_part
        return score

    def search(self, query: str, n: int) -> List[Tuple[int, float]]:
        num = len(self.text_lens)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            scores = list(executor.map(self.calculate_bm25_score, range(num), itertools.repeat(query)))
        scores = list(zip(range(num), scores, strict=False))
        top_n_scores = heapq.nlargest(n, scores, key=lambda x: x[1])
        return top_n_scores

    def add(self, text: str) -> None:
        text_id = len(self.text_lens)
        preprocessed_text = " ".join(tokenizer(text))
        preprocessed_text_split = preprocessed_text.split()
        self.preprocessed_texts.append(preprocessed_text)
        self.sum_len += len(preprocessed_text_split)
        self.word_sets.append(set(preprocessed_text_split))
        self.text_lens.append(len(preprocessed_text_split))
        for word in self.word_sets[text_id]:
            key = f"{word}_{text_id}"
            self.tf_values[key] = self.calculate_tf(word, preprocessed_text)
            if word not in self.idf_values:
                self.idf_values[word] = self.calculate_idf(word)


@dataclass
class BM25Retriever(BaseRetriever):
    persistent_path: str = "data/bm25"
    init_needed: bool = False
    texts: List[str] = field(init=False, default_factory=list)
    metadatas: List[Dict[str, str]] = field(init=False, default_factory=list)
    _data: BM25 = field(init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.persistent_path)
        self.path.mkdir(parents=True, exist_ok=True)
        if self.init_needed:
            self.init()

    def search(self, query: str) -> List[str]:
        if not query or self.is_empty:
            return []
        top_n_scores = self._data.search(query, BaseRetriever.topk)
        return [self.texts[i] for i, _ in top_n_scores]

    def index(self, docs: List[str]):
        logger.info("正在构建索引(SQLite FTS5)...")
        for doc in docs:
            self.add(doc)
        logger.success("索引构建完成")
        self._save()

    def add(self, text: str, metadata: Optional[Dict[str, str]] = None) -> None:
        if not text:
            logger.warning("Text cannot be empty.")
            return
        if text in self.texts:
            logger.warning(f"Text already exists: {text}")
            return
        self.texts.append(text)
        self.metadatas.append(metadata or {})
        self._data.add(text)

    def init(self) -> None:
        self._data = BM25()
        self.texts = []
        self.metadatas = []
        self._save()

    def _save(self) -> None:
        data = self._data.__dict__.copy()
        data["texts"] = self.texts
        data["metadatas"] = self.metadatas
        self.storage.save(data)

    def _load(self) -> None:
        try:
            data = self.storage.load()
            self.texts = data.pop("texts")
            self.metadatas = data.pop("metadatas")
            self._data = BM25(**data)
            return
        except Exception:
            self.init()
