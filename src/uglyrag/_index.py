import logging
from typing import Callable, List

from uglyrag._sqlite import SQLiteStore
from uglyrag._utils import embedding, segment


class Store:
    _instance = None
    segment: Callable[[str], List[str]] = segment
    embedding: Callable[[str], List[float]] = embedding

    @staticmethod
    def get() -> SQLiteStore:
        if Store._instance is None:
            Store._instance = SQLiteStore(Store.segment, Store.embedding)
        return Store._instance


def build(docs: list, vault: str = "Core"):
    store = Store.get()
    if not store.check_table(vault):
        return

    logging.info("Building index...")
    for title, partition, content in docs:
        store.insert_row((title, partition, content))
