import logging

from uglyrag._sqlite import store


def build(docs: list, vault: str = "Core"):
    if not store.check_table(vault):
        return

    logging.info("Building index...")
    for title, partition, content in docs:
        store.insert_row((title, partition, content))
