from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.uglyrag.database.base import Database


class TestDatabase(Database):
    def reset(self):
        super().reset()

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
    return TestDatabase(db_path=Path("/tmp/test.db"), segment=lambda x: x.split(), embedding=lambda x: [0.0] * 128)


def test_post_init(db):
    assert db.dims == 128


def test_check_source(db):
    assert db.check_source("source", "vault")


def test_del_source(db):
    assert db.del_source("source", "vault")


def test_insert_data(db):
    db.insert_data([("source", "id", "content")], "vault")


def test_check_vault(db):
    assert db._check_vault("vault")


def test_background_search_fts(db):
    assert db._background_search_fts("query", "vault") == []


def test_background_search_vec(db):
    assert db._background_search_vec("query", "vault") == []
