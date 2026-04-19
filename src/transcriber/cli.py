"""Command-line interface for transcriber."""

from pathlib import Path
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
    skip_import: Annotated[
        bool,
        typer.Option("--skip-import", help="Skip audio import step"),
    ] = False,
    template: Annotated[
        str | None,
        typer.Option("--template", "-t", help="Output template name"),
    ] = None,
    dictionary: Annotated[
        str | None,
        typer.Option("--dictionary", "-d", help="Additional dictionary YAML file"),
    ] = None,
    sort: Annotated[
        bool,
        typer.Option("--sort", help="Auto-classify transcripts into projects"),
    ] = False,
    no_llm_fallback: Annotated[
        bool,
        typer.Option("--no-llm-fallback", help="Disable LLM fallback for intent routing"),
    ] = False,
) -> None:
    """Run the full transcription pipeline.

    Imports audio from DJI device, transcribes, and processes through LLM.
    """
    from transcriber.pipeline import Pipeline

    config_path = Path(config_file) if config_file else None
    config = load_config(config_path)

    # Override config with CLI flags
    if template:
        config.output.template = template
    if dictionary:
        config.dictionaries.paths.append(dictionary)
    if sort:
        config.classify.enabled = True
    if no_llm_fallback:
        config.router.llm_fallback = False

    console.print("[bold blue]Starting transcription pipeline...[/bold blue]")
    console.print(f"  DJI Source: {config.paths.dji_source}")
    console.print(f"  Output: {config.paths.base}")
    console.print(f"  STT Provider: {config.stt.provider}")
    console.print(f"  LLM Model: {config.llm.model}")
    console.print(f"  Template: {config.output.template}")

    pipeline = Pipeline(config, console=console)
    result = pipeline.run(skip_import=skip_import)

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print(f"  Audio imported: {result.audio_imported}")
    console.print(f"  Transcribed: {result.transcribed}")
    console.print(f"  Processed: {result.processed}")

    if result.classified:
        console.print(f"  Classified: {result.classified}")

    if result.routed:
        console.print(f"  Routed: {result.routed}")

    if result.transcribe_failed or result.process_failed:
        console.print(
            f"  [yellow]Failures: {result.transcribe_failed + result.process_failed}[/yellow]"
        )


@app.command()
def classify(
    file: Annotated[
        str,
        typer.Argument(help="Transcript file to classify"),
    ],
    config_file: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
    rules_file: Annotated[
        str | None,
        typer.Option("--rules", "-r", help="Classification rules YAML file"),
    ] = None,
) -> None:
    """Classify a transcript into a project directory."""
    from transcriber.classify import load_rules, sort_transcript

    config_path = Path(config_file) if config_file else None
    config = load_config(config_path)

    rules_path = Path(rules_file) if rules_file else None
    if not rules_path and config.classify.rules_file:
        rules_path = Path(config.classify.rules_file)

    if not rules_path or not rules_path.exists():
        console.print("[red]No classification rules file found.[/red]")
        raise typer.Exit(1)

    rules = load_rules(rules_path)
    transcript = Path(file)

    if not transcript.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    projects_dir = Path(config.paths.base).expanduser() / "projects"
    result = sort_transcript(transcript, projects_dir, rules)

    console.print(f"Classified: {result.project}/")
    if result.matched_keyword:
        console.print(f"  Matched: {result.matched_keyword}")
    console.print(f"  Moved to: {result.destination}")


@app.command()
def reformat(
    file: Annotated[
        str,
        typer.Argument(help="Transcript file to reformat"),
    ],
    template: Annotated[
        str,
        typer.Option("--template", "-t", help="Template name to apply"),
    ] = "default.md",
) -> None:
    """Reformat an existing transcript with a different template."""
    from transcriber.templates import render_transcript

    transcript = Path(file)
    if not transcript.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    content = transcript.read_text()
    rendered = render_transcript(content, template_name=template)
    transcript.write_text(rendered)

    console.print(f"Reformatted with template: {template}")


@app.command(name="config")
def show_config(
    config_file: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
) -> None:
    """Show current configuration."""
    config_path = Path(config_file) if config_file else None
    config = load_config(config_path)

    console.print("[bold]Current Configuration[/bold]")
    console.print(f"  Base path: {config.paths.base}")
    console.print(f"  DJI source: {config.paths.dji_source}")
    console.print(f"  STT provider: {config.stt.provider}")
    console.print(f"  LLM provider: {config.llm.provider}")
    console.print(f"  LLM model: {config.llm.model}")
    console.print(f"  Template: {config.output.template}")
    console.print(f"  Dictionaries: {config.dictionaries.paths}")
    console.print(f"  Classify enabled: {config.classify.enabled}")
    if config.classify.rules_file:
        console.print(f"  Rules file: {config.classify.rules_file}")


@app.command()
def templates() -> None:
    """List available output templates."""
    from transcriber.templates import list_templates

    available = list_templates()
    console.print("[bold]Available templates:[/bold]")
    for name in available:
        console.print(f"  - {name}")


BUILTIN_MODELFILE_DIR = Path(__file__).parent / "builtin_modelfiles"


@app.command()
def models() -> None:
    """List available Modelfiles for Ollama."""
    import shutil
    import subprocess

    if not BUILTIN_MODELFILE_DIR.is_dir():
        console.print("[red]No built-in Modelfiles found.[/red]")
        raise typer.Exit(1)

    modelfiles = sorted(BUILTIN_MODELFILE_DIR.glob("*.Modelfile"))
    if not modelfiles:
        console.print("[red]No Modelfiles found.[/red]")
        raise typer.Exit(1)

    # Check which Ollama models exist
    existing_models: set[str] = set()
    if shutil.which("ollama"):
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.splitlines():
                if line.strip():
                    existing_models.add(line.split()[0])
        except subprocess.CalledProcessError:
            pass

    console.print("[bold]Available Modelfiles:[/bold]")
    for mf in modelfiles:
        name = mf.stem.replace("-transcriber", "")
        ollama_name = f"transcriber-{name}:latest"
        status = "[green]created[/green]" if ollama_name in existing_models else "[dim]not created[/dim]"
        base_model = ""
        for line in mf.read_text().splitlines():
            if line.startswith("FROM "):
                base_model = line[5:].strip()
                break
        console.print(f"  {name:12s} base={base_model:20s} {status}")

    console.print(f"\nCreate with: [bold]transcriber models-create <name>[/bold]")


@app.command(name="models-create")
def models_create(
    name: Annotated[
        str,
        typer.Argument(help="Model name (e.g., gemma4, qwen3.5, llama3.3)"),
    ],
) -> None:
    """Create an Ollama model from a built-in Modelfile."""
    import subprocess

    modelfile = BUILTIN_MODELFILE_DIR / f"{name}-transcriber.Modelfile"
    if not modelfile.exists():
        available = [
            f.stem.replace("-transcriber", "")
            for f in sorted(BUILTIN_MODELFILE_DIR.glob("*.Modelfile"))
        ]
        console.print(f"[red]Modelfile not found: {name}[/red]")
        console.print(f"Available: {', '.join(available)}")
        raise typer.Exit(1)

    ollama_name = f"transcriber-{name}"
    console.print(f"Creating Ollama model [bold]{ollama_name}[/bold] from {modelfile.name}...")

    try:
        subprocess.run(
            ["ollama", "create", ollama_name, "-f", str(modelfile)],
            check=True,
        )
        console.print(f"[green]Model {ollama_name}:latest created successfully.[/green]")
        console.print(f"\nTo use: set [bold]model = \"{ollama_name}:latest\"[/bold] in config.toml")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to create model: {e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[red]ollama not found. Install from https://ollama.com[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
