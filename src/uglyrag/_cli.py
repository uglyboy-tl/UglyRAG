import logging

import typer

from ._sqlite import SQLiteStore

cli = typer.Typer()
store = SQLiteStore()
# config = Config()


@cli.command()
def add(doc: str, vault: str = "Core"):
    print(f"Hello {doc}")


@cli.command()
def search(query: str, vault: str = "Core"):
    result = store.search(query, vault)
    logging.info(f"Results: {result}")


if __name__ == "__main__":
    cli()
