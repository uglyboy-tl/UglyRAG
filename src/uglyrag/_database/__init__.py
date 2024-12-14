from __future__ import annotations

import logging
from typing import Any

from uglyrag._config import config

from ._database import Database
from ._sqlite import SQLiteStore


def factory_db(*args: Any, **kwargs: Any) -> Database:
    """
    工厂函数，根据配置文件选择数据库类型。
    :return: 数据库对象
    """
    db_type = config.get("db_type")
    if db_type is None or db_type.lower() == "sqlite":
        logging.debug("使用 SQLite 数据库")
        return SQLiteStore(*args, **kwargs)
    elif db_type.lower() == "duckdb":
        try:
            from ._duckdb import DuckDBStore
        except Exception as e:
            raise ImportError("DuckDB 未安装，请先安装 DuckDB") from e
        logging.debug("使用 DuckDB 数据库")
        return DuckDBStore(*args, **kwargs)
    else:
        logging.error(f"不支持的数据库类型: {db_type}")
        raise ValueError(f"不支持的数据库类型: {db_type}")


__all__ = ["Database", "factory_db"]
