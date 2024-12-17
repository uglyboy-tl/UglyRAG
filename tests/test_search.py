from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.uglyrag.search import SearchEngine, merge_results


@patch("src.uglyrag.search.DatabaseManager")
def test_build(mock_db_manager):
    mock_db_manager.reset = MagicMock()
    mock_db_manager.is_source_valid = MagicMock(return_value=False)
    mock_db_manager.add_documents = MagicMock()

    docs = [(1, "test content")]
    SearchEngine.build(docs, reset_db=True)

    mock_db_manager.reset.assert_called_once()
    mock_db_manager.add_documents.assert_called_once()


def test_merge_results():
    results = [[("1", "content1"), ("2", "content2")], [("2", "content2_updated"), ("3", "content3")]]
    expected = {"1": "content1", "2": "content2_updated", "3": "content3"}
    assert merge_results(results) == expected


@patch("src.uglyrag.search.DatabaseManager")
def test_search(mock_db_manager):
    mock_db_manager.search = MagicMock(
        return_value=[[("1", "content1"), ("2", "content2")], [("2", "content2_updated"), ("3", "content3")]]
    )

    results = SearchEngine.search("query")
    expected = [("2", "content2_updated"), ("1", "content1"), ("3", "content3")]

    assert results == expected


@patch("src.uglyrag.search.DatabaseManager")
def test_calculate_rrf(mock_db_manager):
    fts_results = [("1", "content1"), ("2", "content2")]
    vec_results = [("2", "content2_updated"), ("3", "content3")]

    expected = [("2", "content2_updated"), ("1", "content1"), ("3", "content3")]

    results = SearchEngine._calculate_rrf(fts_results, vec_results)
    assert results == expected


@patch("src.uglyrag.search.SearchEngine.rerank", None)
def test_rerank():
    query = "query"
    results = {"1": "content1", "2": "content2", "3": "content3"}
    expected = []

    assert SearchEngine._rerank(query, results) == expected
