"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from transcriber.cli import app

runner = CliRunner()


def test_cli_has_help():
    """CLI should respond to --help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "transcriber" in result.output.lower() or "usage" in result.output.lower()


def test_cli_has_version():
    """CLI should respond to --version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_process_command_exists():
    """CLI should have a process command."""
    result = runner.invoke(app, ["process", "--help"])
    assert result.exit_code == 0
    assert "--template" in result.output
    assert "--dictionary" in result.output
    assert "--sort" in result.output


def test_cli_classify_command_exists():
    """CLI should have a classify command."""
    result = runner.invoke(app, ["classify", "--help"])
    assert result.exit_code == 0
    assert "--rules" in result.output


def test_cli_reformat_command_exists():
    """CLI should have a reformat command."""
    result = runner.invoke(app, ["reformat", "--help"])
    assert result.exit_code == 0
    assert "--template" in result.output


def test_cli_config_command_exists():
    """CLI should have a config command."""
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "Base path" in result.output or "base" in result.output.lower()


def test_cli_templates_command_lists_templates():
    """CLI should list available templates."""
    result = runner.invoke(app, ["templates"])
    assert result.exit_code == 0
    assert "default.md" in result.output


def test_cli_reformat_applies_template(tmp_path: Path):
    """Reformat should apply template to a file."""
    transcript = tmp_path / "test.md"
    transcript.write_text("My transcript content.")

    result = runner.invoke(app, ["reformat", str(transcript), "--template", "summary.md"])
    assert result.exit_code == 0

    content = transcript.read_text()
    assert "Summary" in content
    assert "My transcript content." in content


def test_cli_process_no_llm_fallback_flag():
    """CLI should accept --no-llm-fallback flag."""
    result = runner.invoke(app, ["process", "--help"])
    assert "--no-llm-fallback" in result.output


def test_cli_models_command_exists():
    """CLI should have a models command that lists available Modelfiles."""
    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "gemma4" in result.output
    assert "qwen3.5" in result.output
    assert "llama3.3" in result.output


def test_cli_models_create_help():
    """models create should show help with available model names."""
    result = runner.invoke(app, ["models-create", "--help"])
    assert result.exit_code == 0
    assert "name" in result.output.lower()


def test_cli_models_create_invalid_name():
    """models create should reject unknown model names."""
    result = runner.invoke(app, ["models-create", "nonexistent"])
    assert result.exit_code != 0 or "not found" in result.output.lower()
