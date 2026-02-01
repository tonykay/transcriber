"""Command-line interface for transcriber."""

from typing import Annotated

import typer
from rich.console import Console

from transcriber import __version__
from transcriber.config import load_config

app = typer.Typer(
    name="transcriber",
    help="Voice capture and processing system for DJI audio recordings.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"transcriber {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Transcriber - Voice capture and processing system."""
    pass


@app.command()
def process(
    config_file: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
) -> None:
    """Run the full transcription pipeline.

    Imports audio from DJI device, transcribes, and processes through LLM.
    """
    from pathlib import Path

    config_path = Path(config_file) if config_file else None
    config = load_config(config_path)

    console.print("[bold blue]Starting transcription pipeline...[/bold blue]")
    console.print(f"  DJI Source: {config.paths.dji_source}")
    console.print(f"  Output: {config.paths.base}")
    console.print(f"  STT Provider: {config.stt.provider}")
    console.print(f"  LLM Model: {config.llm.model}")

    # TODO: Implement pipeline steps
    console.print("[yellow]Pipeline not yet implemented[/yellow]")


if __name__ == "__main__":
    app()
