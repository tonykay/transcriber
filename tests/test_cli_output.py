"""Tests for output directory CLI options."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from transcriber.cli import app
from transcriber.config import TranscriberConfig

runner = CliRunner()


@pytest.mark.parametrize("output_dir", ["./alternate output", "~/alternate-output"])
def test_process_output_dir_overrides_config(tmp_path: Path, output_dir: str):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[paths]\nbase = "/configured-output"\n')

    with patch("transcriber.pipeline.Pipeline") as pipeline:
        result = runner.invoke(
            app,
            ["process", "--config", str(config_file), "--output-dir", output_dir],
        )

    assert result.exit_code == 0, result.output
    config = pipeline.call_args.args[0]
    base = Path(output_dir).expanduser()
    assert Path(config.paths.base) == base
    assert Path(config.paths.transcripts) == base / "transcripts"
    for name in ("audio_unprocessed", "audio_processed", "text_unprocessed", "text_processed"):
        assert Path(getattr(config.paths, name)) == base / ".processing" / name.replace("_", "-")
    pipeline.return_value.run.assert_called_once_with(skip_import=False)
    assert config_file.read_text() == '[paths]\nbase = "/configured-output"\n'


def test_process_preserves_configured_output_without_flag():
    config = TranscriberConfig()
    config.paths.base = "/configured-output"
    with (
        patch("transcriber.cli.load_config", return_value=config),
        patch("transcriber.pipeline.Pipeline") as pipeline,
    ):
        result = runner.invoke(app, ["process", "--skip-import"])

    assert result.exit_code == 0, result.output
    assert pipeline.call_args.args[0].paths.base == "/configured-output"
    pipeline.return_value.run.assert_called_once_with(skip_import=True)


def test_list_output_dirs_uses_defaults_without_side_effects(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with (
        patch("transcriber.cli.load_config") as load_config,
        patch("transcriber.pipeline.Pipeline") as pipeline,
    ):
        result = runner.invoke(app, ["--list-output-dirs"], terminal_width=240)

    assert result.exit_code == 0, result.output
    base = tmp_path / "Resources" / "Transcripts"
    for target in (
        "transcripts", "projects", "article-ideas", "blogs", "todos.md", "notes.md",
        ".processing/audio-unprocessed", ".processing/audio-processed",
        ".processing/text-unprocessed", ".processing/text-processed",
    ):
        assert str(base / target) in result.output
    assert result.output.count(str(base / "todos.md")) == 1
    assert "files" in result.output.lower()
    load_config.assert_not_called()
    pipeline.assert_not_called()
    assert not base.exists()


def test_output_options_appear_in_help():
    assert "--list-output-dirs" in runner.invoke(app, ["--help"]).output
    assert "--output-dir" in runner.invoke(app, ["process", "--help"]).output
