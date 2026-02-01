"""Tests for CLI module."""

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
