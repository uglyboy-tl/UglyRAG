import logging

from uglyrag._embed import Embedder
from uglyrag._sqlite import store
from uglyrag._tokenize import tokenize


def build(docs: list, vault: str = "Core"):
    if not store.check_table(vault):
        return

    logging.info("Building index...")
    for title, partition, content in docs:
        indexed_content = " ".join(tokenize(content) + tokenize(str(title)))
        embedding = Embedder.embedding(content)
        store.insert_row(((title, partition, content), indexed_content, embedding))
