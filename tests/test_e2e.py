"""End-to-end tests for transcriber pipeline."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from transcriber.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dirs(tmp_path: Path) -> dict[str, Path]:
    """Create temporary directory structure for testing."""
    base = tmp_path / "transcripts"

    # Create DJI source with test file
    dji_source = tmp_path / "DJI_MIC2"
    dji_audio = dji_source / "DJI_Audio_001"
    dji_audio.mkdir(parents=True)
    (dji_audio / "DJI_01_20250702_175446.WAV").write_bytes(b"fake audio data")

    return {
        "base": base,
        "dji_source": dji_source,
    }


def test_full_pipeline_with_mocked_externals(temp_dirs: dict[str, Path], tmp_path: Path) -> None:
    """Full pipeline should work with mocked STT and LLM."""
    # Create config file
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(f'''
[paths]
base = "{temp_dirs["base"]}"
dji_source = "{temp_dirs["dji_source"]}"

[stt]
provider = "parakeet"

[llm]
provider = "ollama"
model = "transcriber:latest"
''')

    def mock_stt_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
        """Mock subprocess.run for parakeet-mlx STT."""
        cmd = args[0]
        if isinstance(cmd, list) and len(cmd) > 0:
            if cmd[0] == "parakeet-mlx":
                # Find the output-dir from command args
                try:
                    output_dir_idx = cmd.index("--output-dir")
                    output_dir = Path(cmd[output_dir_idx + 1])
                    audio_file = Path(cmd[1])
                    output_file = output_dir / f"{audio_file.stem}.txt"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("This is transcribed text from the audio.")
                except (ValueError, IndexError):
                    pass
                return MagicMock(returncode=0, stdout="", stderr="")
            elif cmd[0] == "ollama":
                # Return processed markdown
                return MagicMock(
                    returncode=0,
                    stdout="# Processed Transcript\n\nThis is the LLM-processed text.",
                    stderr="",
                )
        return MagicMock(returncode=0, stdout="", stderr="")

    # Mock shutil.which to make both tools appear available
    def mock_which(cmd: str) -> str | None:
        if cmd in ("parakeet-mlx", "ollama"):
            return f"/usr/bin/{cmd}"
        return None

    with (
        patch("shutil.which", side_effect=mock_which),
        patch("subprocess.run", side_effect=mock_stt_subprocess),
    ):
        result = runner.invoke(app, ["process", "--config", str(config_file)])

    # Verify pipeline ran without critical errors
    assert result.exit_code == 0
    assert "Pipeline complete" in result.output


def test_pipeline_skip_import_with_existing_audio(
    temp_dirs: dict[str, Path], tmp_path: Path
) -> None:
    """Pipeline should work with --skip-import when audio already exists."""
    # Create config file
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(f'''
[paths]
base = "{temp_dirs["base"]}"
dji_source = "{temp_dirs["dji_source"]}"

[stt]
provider = "parakeet"

[llm]
provider = "ollama"
model = "transcriber:latest"
''')

    # Pre-create audio in the unprocessed directory with correct ISO format
    audio_unprocessed_dir = temp_dirs["base"] / ".processing" / "audio-unprocessed"
    audio_unprocessed_dir.mkdir(parents=True)
    (audio_unprocessed_dir / "2025-07-02-17:54:46.WAV").write_bytes(b"fake audio data")

    def mock_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
        """Mock subprocess.run for STT and LLM."""
        cmd = args[0]
        if isinstance(cmd, list) and len(cmd) > 0:
            if cmd[0] == "parakeet-mlx":
                try:
                    output_dir_idx = cmd.index("--output-dir")
                    output_dir = Path(cmd[output_dir_idx + 1])
                    audio_file = Path(cmd[1])
                    output_file = output_dir / f"{audio_file.stem}.txt"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("Transcribed text from skip-import test.")
                except (ValueError, IndexError):
                    pass
                return MagicMock(returncode=0, stdout="", stderr="")
            elif cmd[0] == "ollama":
                return MagicMock(
                    returncode=0,
                    stdout="# Enhanced Transcript\n\nProcessed content here.",
                    stderr="",
                )
        return MagicMock(returncode=0, stdout="", stderr="")

    def mock_which(cmd: str) -> str | None:
        if cmd in ("parakeet-mlx", "ollama"):
            return f"/usr/bin/{cmd}"
        return None

    with (
        patch("shutil.which", side_effect=mock_which),
        patch("subprocess.run", side_effect=mock_subprocess),
    ):
        result = runner.invoke(app, ["process", "--config", str(config_file), "--skip-import"])

    assert result.exit_code == 0
    assert "Pipeline complete" in result.output


def test_pipeline_handles_missing_stt_provider(temp_dirs: dict[str, Path], tmp_path: Path) -> None:
    """Pipeline should handle missing STT provider gracefully."""
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(f'''
[paths]
base = "{temp_dirs["base"]}"
dji_source = "{temp_dirs["dji_source"]}"

[stt]
provider = "parakeet"

[llm]
provider = "ollama"
model = "transcriber:latest"
''')

    # Pre-create audio to skip import
    audio_unprocessed_dir = temp_dirs["base"] / ".processing" / "audio-unprocessed"
    audio_unprocessed_dir.mkdir(parents=True)
    (audio_unprocessed_dir / "2025-07-02-17:54:46.WAV").write_bytes(b"fake audio")

    # Return None for parakeet-mlx (not installed)
    def mock_which(cmd: str) -> str | None:
        if cmd == "ollama":
            return "/usr/bin/ollama"
        return None

    with patch("shutil.which", side_effect=mock_which):
        result = runner.invoke(app, ["process", "--config", str(config_file), "--skip-import"])

    # Pipeline should complete even if STT not available
    assert result.exit_code == 0
    assert "not available" in result.output.lower() or "Pipeline complete" in result.output


def test_pipeline_creates_output_directories(temp_dirs: dict[str, Path], tmp_path: Path) -> None:
    """Pipeline should create necessary output directories."""
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(f'''
[paths]
base = "{temp_dirs["base"]}"
dji_source = "{temp_dirs["dji_source"]}"

[stt]
provider = "parakeet"

[llm]
provider = "ollama"
model = "transcriber:latest"
''')

    def mock_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
        cmd = args[0]
        if isinstance(cmd, list) and len(cmd) > 0:
            if cmd[0] == "parakeet-mlx":
                try:
                    output_dir_idx = cmd.index("--output-dir")
                    output_dir = Path(cmd[output_dir_idx + 1])
                    audio_file = Path(cmd[1])
                    output_file = output_dir / f"{audio_file.stem}.txt"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("Test transcript content.")
                except (ValueError, IndexError):
                    pass
                return MagicMock(returncode=0, stdout="", stderr="")
            elif cmd[0] == "ollama":
                return MagicMock(
                    returncode=0,
                    stdout="# Final Transcript\n\nEnhanced content.",
                    stderr="",
                )
        return MagicMock(returncode=0, stdout="", stderr="")

    def mock_which(cmd: str) -> str | None:
        if cmd in ("parakeet-mlx", "ollama"):
            return f"/usr/bin/{cmd}"
        return None

    with (
        patch("shutil.which", side_effect=mock_which),
        patch("subprocess.run", side_effect=mock_subprocess),
    ):
        result = runner.invoke(app, ["process", "--config", str(config_file)])

    assert result.exit_code == 0

    # Verify key directories were created
    assert (temp_dirs["base"] / ".processing" / "audio-unprocessed").exists()
    assert (temp_dirs["base"] / ".processing" / "audio-processed").exists()
    assert (temp_dirs["base"] / ".processing" / "text-unprocessed").exists() or (
        temp_dirs["base"] / ".processing" / "text-processed"
    ).exists()


def test_router_dispatches_todo_to_file(tmp_path: Path) -> None:
    """Router should extract a todo and append it to todos.md."""
    from datetime import datetime
    from transcriber.dispatch import append_to_file
    from transcriber.intents import load_intents
    from transcriber.router import route_text

    # Create intents config
    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: todo
    triggers:
      - "todo"
    output: append
    target: "todos.md"
  - type: todo
    triggers:
      - "speak to {person} about"
    output: append
    target: "todos.md"
    extract:
      person: frontmatter
""")
    intents = load_intents(intents_file)

    # Route a transcript with a start trigger
    result = route_text("Todo watch the Nvidia keynote especially the OpenClaw bit", intents)
    assert result.primary_intent == "todo"
    assert len(result.extracted_intents) == 1

    # Dispatch the intent
    todos_file = tmp_path / "todos.md"
    intent = result.extracted_intents[0]
    append_to_file(
        target=todos_file,
        intent=intent,
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
    )

    content = todos_file.read_text()
    assert "- [ ]" in content
    assert "Nvidia keynote" in content
    assert "DJI_0042.WAV" in content


def test_router_extracts_embedded_intents(tmp_path: Path) -> None:
    """Router should extract embedded todos from a brain dump."""
    from datetime import datetime
    from transcriber.dispatch import append_to_file
    from transcriber.intents import load_intents
    from transcriber.router import route_text

    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: todo
    triggers:
      - "todo"
      - "reminder"
    output: append
    target: "todos.md"
  - type: article_idea
    triggers:
      - "article idea"
    output: file
    target: "article-ideas/"
""")
    intents = load_intents(intents_file)

    text = (
        "Article idea about voice-first productivity tools. "
        "They let you capture thoughts on the go. "
        "Todo check out the latest whisper models. "
        "Reminder to update the blog."
    )
    result = route_text(text, intents)

    assert result.primary_intent == "article_idea"
    # Should find the start trigger + at least 1 embedded todo
    todo_intents = [i for i in result.extracted_intents if i.type == "todo"]
    assert len(todo_intents) >= 1

    # Dispatch todos
    todos_file = tmp_path / "todos.md"
    for intent in result.extracted_intents:
        if intent.type == "todo":
            append_to_file(
                target=todos_file,
                intent=intent,
                date=datetime(2026, 3, 30, 14, 32),
                source="DJI_0042.WAV",
                source_transcript="transcript-DJI_0042.md",
            )

    if todos_file.exists():
        content = todos_file.read_text()
        assert "whisper models" in content.lower() or "update the blog" in content.lower()


def test_frontmatter_on_transcript(tmp_path: Path) -> None:
    """Full transcript should get frontmatter with tags."""
    from datetime import datetime
    from transcriber.frontmatter import generate_frontmatter

    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#article_idea", "#summit_lab", "#ai"],
        intent="article_idea",
        project="summit-lab",
    )

    transcript_text = "This is my transcript about the summit lab."
    full_output = fm + "\n" + transcript_text

    assert full_output.startswith("---\n")
    assert "#article_idea" in full_output
    assert "summit-lab" in full_output
    assert transcript_text in full_output
