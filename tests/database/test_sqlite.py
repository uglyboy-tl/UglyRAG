from __future__ import annotations

from pathlib import Path

import pytest

from uglyrag.database._sqlite import SQLiteDatebase


@pytest.fixture
def sqlite():
    def segment(x):
        return x.split()

    def embedding(x):
        return [0.1, 0.2, 0.3]

    return SQLiteDatebase(Path("/tmp/test.db"), segment, embedding)


@pytest.fixture
def reset_database(sqlite):
    sqlite.reset()
    sqlite._check_vault("vault")
    sqlite.insert_data([("source", "part_id", "content")], "vault")


def test_sqlite_init(sqlite):
    assert sqlite.db_path == Path("/tmp/test.db")
    assert sqlite.dims == 3


def test_sqlite_reset(sqlite):
    sqlite.reset()
    assert True  # Add more specific assertions as needed


def test_sqlite_check_vault(sqlite):
    assert sqlite._check_vault("vault")


def test_sqlite_insert_data(sqlite):
    sqlite._check_vault("vault")
    sqlite.insert_data([("source", "part_id", "content")], "vault")
    assert True  # Add more specific assertions as needed


def test_sqlite_rebuild_index(sqlite, reset_database):
    sqlite.rebuild_index("vault")
    assert True  # Add more specific assertions as needed


def test_sqlite_check_source(sqlite, reset_database):
    assert sqlite.check_source("source", "vault")


def test_sqlite_del_source(sqlite, reset_database):
    assert sqlite.del_source("source", "vault")


def test_sqlite_background_search_fts(sqlite, reset_database):
    results = sqlite._background_search_fts("query", "vault")
    assert isinstance(results, list)


def test_sqlite_background_search_vec(sqlite, reset_database):
    results = sqlite._background_search_vec("query", "vault")
    assert isinstance(results, list)
