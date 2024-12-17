from __future__ import annotations

from pathlib import Path

import pytest

from uglyrag.database._duckdb import DuckDBDatabase


@pytest.fixture
def duckdb():
    def segment(x):
        return x.split()

    def embedding(x):
        return [0.1, 0.2, 0.3]

    return DuckDBDatabase(Path("/tmp/test.ddb"), segment, embedding)


@pytest.fixture
def reset_database(duckdb):
    duckdb.reset()
    duckdb._check_vault("vault")
    duckdb.insert_data([("source", "part_id", "content")], "vault")


def test_duckdb_init(duckdb):
    assert duckdb.db_path == Path("/tmp/test.ddb")
    assert duckdb.dims == 3


def test_duckdb_reset(duckdb):
    duckdb.reset()
    assert True  # Add more specific assertions as needed


def test_duckdb_check_vault(duckdb):
    assert duckdb._check_vault("vault")


def test_duckdb_insert_data(duckdb):
    duckdb._check_vault("vault")
    duckdb.insert_data([("source", "part_id", "content")], "vault")
    assert True  # Add more specific assertions as needed


def test_duckdb_rebuild_index(duckdb, reset_database):
    duckdb.rebuild_index("vault")
    assert True  # Add more specific assertions as needed


def test_duckdb_check_source(duckdb, reset_database):
    assert duckdb.check_source("source", "vault")


def test_duckdb_del_source(duckdb, reset_database):
    assert duckdb.del_source("source", "vault")


def test_duckdb_background_search_fts(duckdb, reset_database):
    duckdb.rebuild_index("vault")
    results = duckdb._background_search_fts("query", "vault")
    assert isinstance(results, list)


def test_duckdb_background_search_vec(duckdb, reset_database):
    results = duckdb._background_search_vec("query", "vault")
    assert isinstance(results, list)
