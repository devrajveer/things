import typer
from typing import Optional

app = typer.Typer(
    name="yp",
    help="MegaIoT CLI tool",
    add_completion=False,
)

__version__ = "0.1.0"

def version_callback(value: bool):
    if value:
        typer.echo(f"yp CLI version: {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=version_callback,
        is_eager=True,
    )
):
    """
    MegaIoT Platform CLI
    """
    pass

@app.command()
def info():
    """
    Show information about the CLI.
    """
    typer.echo("MegaIoT Platform CLI")

if __name__ == "__main__":
    app()
