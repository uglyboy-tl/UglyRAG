import logging

import typer

from uglyrag._search import hybrid_search

cli = typer.Typer()


@cli.command()
def add(doc: str, vault: str = "Core"):
    print(f"Hello {doc}")


@cli.command()
def search(query: str, vault: str = "Core"):
    result = hybrid_search(query, vault)
    logging.info(f"Results: {result}")


if __name__ == "__main__":
    cli()
