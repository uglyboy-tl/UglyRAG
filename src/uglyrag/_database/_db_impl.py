from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Database(ABC):
    segment: Callable[[str], list[str]]
    embedding: Callable[[str], list[float]]

    @abstractmethod
    def check_table(self) -> bool:
        pass

    @abstractmethod
    def insert_row(self, doc: tuple[str], vault: str):
        pass

    @abstractmethod
    def check_source(self, source: str, vault: str) -> bool:
        pass

    @abstractmethod
    def rm_source(self, source: str, vault: str):
        pass

    @abstractmethod
    def search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        pass

    @abstractmethod
    def search_vec(self, query: list[float], vault: str, top_n: int = 5) -> list[tuple[str, float]]:
        pass
