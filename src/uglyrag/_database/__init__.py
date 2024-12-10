from __future__ import annotations

import logging

from uglyrag._config import config

from ._db_impl import Database
from ._sqlite import SQLiteStore


def factory_db(*args, **kwargs) -> Database:
    """
    Create a new database instance.

    Args:
        uri (str): The URI of the database.
        kwargs: Additional arguments to pass to the database constructor.

    Returns:
        Database: The new database instance.
    """
    database_type = config.get("database")
    if database_type is None or database_type.lower() == "sqlite":
        logging.debug("使用 SQLite 数据库")
        return SQLiteStore(*args, **kwargs)
    elif database_type.lower() == "duckdb":
        logging.debug("使用 DuckDB 数据库")
        raise NotImplementedError("DuckDB 数据库暂未实现")
    else:
        logging.error(f"不支持的数据库类型: {database_type}")


__all__ = ["Database", "factory_db"]
