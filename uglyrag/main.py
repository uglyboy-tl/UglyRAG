import logging

import typer

from .sqlite import SQLiteStore

app = typer.Typer()
store = SQLiteStore()
# config = Config()


@app.command()
def add(doc: str, vault: str = "Core"):
    print(f"Hello {doc}")


@app.command()
def search(query: str, vault: str = "Core"):
    result = store.search(query, vault)
    logging.info(f"Results: {result}")


if __name__ == "__main__":
    app()
