from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uglyrag.db_manager import DatabaseManager


@pytest.fixture(autouse=True)
def clear_cache():
    DatabaseManager._check_vault_dict.clear()


@pytest.fixture
def mock_database():
    with patch("uglyrag.db_manager.Database") as mock_database:
        mock_instance = mock_database.return_value
        mock_instance._check_vault.return_value = True
        mock_instance.__enter__.return_value = mock_instance
        yield mock_database


@pytest.fixture
def mock_config():
    with patch("uglyrag.db_manager.config") as mock_config:
        mock_config.get.side_effect = lambda key: "sqlite" if key == "db_type" else "test.db"
        mock_config.data_dir = Path("/mock/path")
        yield mock_config


def test_get_database(mock_config, mock_database):
    with patch("uglyrag.database._sqlite.sqlite3.connect") as mock_connect:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("3.35.5", "0.1.0")  # 模拟版本信息
        mock_connect.return_value.execute.return_value = mock_cursor
        db_instance = DatabaseManager.get_database()
        assert db_instance is not None
        mock_connect.assert_called_once()


def test_reset(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database.return_value):
        DatabaseManager.reset()
        mock_database.return_value.reset.assert_called_once()


def test_search(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database.return_value):
        with patch("uglyrag.db_manager.asyncio.run") as mock_run:
            DatabaseManager.search("query", "vault")
            mock_run.assert_called_once()


def test_add_documents(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database.return_value):
        with patch.object(DatabaseManager, "_is_vault_valid", return_value=True):
            data = [("source", "title", "content")]
            DatabaseManager.add_documents(data, "vault")
            mock_database.return_value.insert_data.assert_called_once_with(data, "vault")
            mock_database.return_value.rebuild_index.assert_called_once_with("vault")


def test_is_source_valid(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database.return_value):
        mock_database.return_value.check_source.return_value = True
        assert DatabaseManager.is_source_valid("source", "vault")
        mock_database.return_value.check_source.assert_called_once_with("source", "vault")


def test_get_embedding():
    text = "sample text"
    embedding = DatabaseManager._get_embedding(text)
    assert embedding is not None


def test_is_vault_valid(mock_database):
    with patch.object(DatabaseManager, "get_database") as mock_get_database:
        mock_db_instance = mock_get_database.return_value.__enter__.return_value
        DatabaseManager._is_vault_valid("vault")
        mock_db_instance._check_vault.assert_called_once_with("vault")


@pytest.mark.asyncio
async def test_async_search(mock_database):
    with patch.object(DatabaseManager, "get_database", return_value=mock_database.return_value):
        with patch("uglyrag.db_manager.asyncio.gather", new_callable=AsyncMock) as mock_gather:
            with patch.object(DatabaseManager, "_is_vault_valid", return_value=True):
                with patch.object(DatabaseManager, "_run_in_executor", new_callable=AsyncMock) as mock_run:
                    mock_run.side_effect = [[], []]  # 模拟两次调用的返回值
                    result = await DatabaseManager._async_search("query", "vault")
                    assert result is not None
                    mock_gather.assert_awaited_once()
                    assert mock_run.call_count == 2
