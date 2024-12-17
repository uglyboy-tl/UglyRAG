from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from uglyrag.db_manager import DatabaseManager


@pytest.fixture
def mock_database():
    with patch("uglyrag.db_manager.Database") as mock_database:
        yield mock_database


@pytest.fixture
def mock_config():
    with patch("uglyrag.db_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key: "sqlite" if key == "db_type" else "test.db"
        mock_config.data_dir = MagicMock()
        mock_config.data_dir.__truediv__.return_value = Path("/mock/path")
        yield mock_config


def test_get_database(mock_config, mock_database):
    db_instance = DatabaseManager.get_database()
    assert db_instance is not None
    mock_database.assert_called_once()


def test_reset(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database):
        DatabaseManager.reset()
        mock_database.reset.assert_called_once()


def test_search(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database):
        with patch("uglyrag.db_manager.asyncio.run") as mock_run:
            DatabaseManager.search("query", "vault")
            mock_run.assert_called_once()


def test_add_documents(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database):
        data = [("source", "title", "content")]
        DatabaseManager.add_documents(data, "vault")
        mock_database.insert_data.assert_called_once_with(data, "vault")
        mock_database.rebuild_index.assert_called_once_with("vault")


def test_is_source_valid(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database):
        mock_database.check_source.return_value = True
        assert DatabaseManager.is_source_valid("source", "vault")
        mock_database.check_source.assert_called_once_with("source", "vault")


def test_get_embedding():
    text = "sample text"
    embedding = DatabaseManager._get_embedding(text)
    assert embedding is not None


def test_is_vault_valid(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database):
        mock_database._check_vault.return_value = True
        assert DatabaseManager._is_vault_valid("vault")
        mock_database._check_vault.assert_called_once_with("vault")


def test_async_search(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database):
        with patch("uglyrag.db_manager.asyncio.gather") as mock_gather:
            result = DatabaseManager._async_search("query", "vault")
            assert result is not None
            mock_gather.assert_called_once()
