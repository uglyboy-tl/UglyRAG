import logging
import sqlite3

import sqlite_vec

from .config import Config

config = Config()

weight_fts = int(config.get("weight_fts", "RRF", 1))
weight_vec = int(config.get("weight_vec", "RRF", 1))
k = int(config.get("k", "RRF", 60))


def reciprocal_rank_fusion(fts_results, vec_results):
    rank_dict = {}

    # Process FTS results
    for rank, (id,) in enumerate(fts_results):
        if id not in rank_dict:
            rank_dict[id] = 0
        rank_dict[id] += 1 / (k + rank + 1) * weight_fts

    # Process vector results
    for rank, (rowid, _) in enumerate(vec_results):
        if rowid not in rank_dict:
            rank_dict[rowid] = 0
        rank_dict[rowid] += 1 / (k + rank + 1) * weight_vec

    # Sort by RRF score
    sorted_results = sorted(rank_dict.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def connect_to_database(db_path):
    """
    连接到数据库并返回连接对象。
    :param db_path: 数据库文件路径
    :return: SQLite 连接对象
    """
    try:
        sqlite_conn = sqlite3.connect(db_path)
        logging.info(f"已连接到数据库: {db_path}")
        return sqlite_conn
    except sqlite3.Error as e:
        logging.error(f"连接数据库失败: {e}")
        raise


def load_extensions(sqlite_conn):
    """
    加载 SQLite 扩展。
    :param sqlite_conn: SQLite 连接对象
    """
    try:
        sqlite_conn.enable_load_extension(True)
        sqlite_vec.load(sqlite_conn)
        logging.info("SQLite 扩展 `sqlite_vec` 加载成功")
    finally:
        sqlite_conn.enable_load_extension(False)


def initialize_database():
    """
    初始化数据库连接和扩展。
    :return: SQLite 连接对象
    """
    db_filename = config.get("db_name", "core", "database.db")
    db_path = config.data_dir / db_filename
    sqlite_conn = connect_to_database(db_path)
    load_extensions(sqlite_conn)
    return sqlite_conn


def get_database_versions(sqlite_conn):
    """
    获取 SQLite 和 vec 扩展的版本信息。
    :return: SQLite 版本和 vec 扩展版本
    """
    try:
        sqlite_version, vec_version = sqlite_conn.execute("SELECT sqlite_version(), vec_version()").fetchone()
        logging.info(f"SQLite版本：{sqlite_version}, sqlite_vec 版本：{vec_version}")
        return sqlite_version, vec_version
    except sqlite3.Error as e:
        logging.error(f"执行 SQL 失败: {e}")
        raise
