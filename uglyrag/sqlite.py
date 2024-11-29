import logging

from ._sqlite import get_database_versions, initialize_database
from .tokenize import tokenize


def or_words(query):
    words = tokenize(query)
    result = " OR ".join(words)
    return result


class SQLiteStore:
    def __init__(self):
        self.conn = initialize_database()
        get_database_versions(self.conn)
        self.cursor = self.conn.cursor()

    def _check_table(self, vault: str):
        pass

    def create_table(self, vault: str):
        dims = 512

        # 创建表
        # 创建数据表
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {vault} (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, partition TEXT, title TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);"
        )
        # 创建全文搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_fts USING fts5(indexed_content);")
        # 创建向量搜索表
        self.cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {vault}_vec USING vec0(embedding FLOAT[{str(dims)}]);")

        """
        # 创建触发器保持表同步
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ai AFTER INSERT ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts(rowid, content, title) VALUES (new.id, new.content, new.title); "
            f"END;"
        )
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_ad AFTER DELETE ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts({vault}_fts,rowid, content, title) VALUES ('delete',old.id, old.content, old.title); "
            f"END;"
        )
        self.cursor.execute(
            f"CREATE TRIGGER IF NOT EXISTS {vault}_au AFTER UPDATE ON {vault} BEGIN "
            f"INSERT INTO {vault}_fts({vault}_fts,rowid, content, title) VALUES ('delete',old.id, old.content, old.title); "
            f"INSERT INTO {vault}_fts(rowid, content, title) VALUES (new.id, new.content, new.title); "
            f"END;"
        )
        """

        # 提交更改
        self.conn.commit()

    # 批量插入数据
    def insert_row(self, data, vault="Core"):
        logging.debug(f"正在插入数据到数据库: {data}")
        self._check_table(vault)
        self.cursor.execute(f"INSERT INTO {vault} (title, partition, content) VALUES (?,?,?)", data)
        title, _, content = data
        indexed_content = " ".join(tokenize(content) + tokenize(title))
        self.cursor.execute(f"INSERT INTO {vault}_fts (indexed_content) VALUES (?)", (indexed_content,))

        # 提交更改
        self.conn.commit()

    def search(self, query: str, vault="Core", top_n: int = 5):
        self._check_table(vault)
        self.cursor.execute(
            f"SELECT {vault}.id, {vault}.content FROM {vault}_fts join {vault} on {vault}_fts.rowid={vault}.id WHERE {vault}_fts MATCH ? ORDER BY bm25({vault}_fts) LIMIT ?",
            (or_words(query), top_n),
        )
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()
