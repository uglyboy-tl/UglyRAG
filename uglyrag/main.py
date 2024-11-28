import typer

app = typer.Typer()

@app.command()
def add(doc:str, vault: str = "default"):
    print(f"Hello {doc}")

@app.command()
def search(query: str, vault: str = "default"):
    print(f"Hello {query}")


if __name__ == "__main__":
    app()
