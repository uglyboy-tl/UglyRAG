from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from uglyrag.database.base import Database


class ConcreteDatabase(Database):
    def reset(self) -> None:
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
    return ConcreteDatabase(
        db_path=Path("/tmp/test.db"), segment=lambda x: x.split(), embedding=lambda x: [0.1, 0.2, 0.3]
    )


def test_post_init(db):
    assert db.dims == 3


def test_invalid_db_path():
    with pytest.raises(ValueError):
        ConcreteDatabase(
            db_path=Path("/tmp/test.txt"), segment=lambda x: x.split(), embedding=lambda x: [0.1, 0.2, 0.3]
        )


def test_enter_exit(db):
    with db as database:
        assert database is db


@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.unlink")
def test_reset(mock_unlink, mock_exists, db):
    db.reset()
    mock_unlink.assert_called_once()


def test_rebuild_index(db):
    db.rebuild_index("vault")


def test_check_source(db):
    assert db.check_source("source", "vault") is True


def test_del_source(db):
    assert db.del_source("source", "vault") is True


def test_insert_data(db):
    db.insert_data([("source", "id", "content")], "vault")


def test_check_vault(db):
    assert db._check_vault("vault")


def test_background_search_fts(db):
    assert db._background_search_fts("query", "vault") == []


def test_background_search_vec(db):
    assert db._background_search_vec("query", "vault") == []
