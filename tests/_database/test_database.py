from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from uglyrag.database.base import Database


class TestDatabase(Database):
    def reset(self):
        pass

    def check_source(self, source: str, vault: str) -> bool:
        return True

    def del_source(self, source: str, vault: str) -> bool:
        return True

    def insert_data(self, data: list[tuple[str, str, str]], vault: str) -> None:
        pass

    def _check_vault(self, vault: str) -> bool:
        return True

    def _background_search_fts(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        return []

    def _background_search_vec(self, query: str, vault: str, top_n: int = 5) -> list[tuple[str, str]]:
        return []


@pytest.fixture
def db():
    segment = Mock(return_value=["hello", "world"])
    embedding = Mock(return_value=[0.1, 0.2, 0.3])
    return TestDatabase(Path("/tmp/test.db"), segment, embedding)


def test_database_init(db):
    assert db.db_path == Path("/tmp/test.db")
    assert db.dims == 3


def test_database_reset(db):
    db.reset()
    assert True  # Add more specific assertions as needed


def test_database_check_source(db):
    assert db.check_source("source", "vault")


def test_database_del_source(db):
    assert db.del_source("source", "vault")


def test_database_insert_data(db):
    db.insert_data([("source", "part_id", "content")], "vault")
    assert True  # Add more specific assertions as needed


def test_database_check_vault(db):
    assert db.check_vault("vault")


def test_database_search(db):
    results = db.search("query", "vault")
    assert isinstance(results, list)
