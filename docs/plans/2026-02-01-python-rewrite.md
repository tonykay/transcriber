# Python Rewrite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite the transcriber bash script in Python with a library + CLI architecture, matching current functionality while enabling future extensions (term correction, templates, auto-classification).

**Architecture:** Core library in `src/transcriber/` with independent modules for each pipeline stage (audio import, transcription, text processing). Thin CLI wrapper using Typer. Configuration via TOML with sensible defaults. Speech-to-text provider is pluggable (parakeet default, whisper future).

**Tech Stack:** Python 3.13, uv for packaging, Typer (CLI), tomllib (config), Pydantic (structured data), pytest (testing)

---

## Phase 1: Project Scaffolding

### Task 1: Initialize uv Project

**Files:**
- Create: `pyproject.toml`
- Create: `src/transcriber/__init__.py`
- Create: `src/transcriber/py.typed`

**Step 1: Create pyproject.toml with uv**

```bash
cd /Users/tok/Dropbox/PARAL/Projects/transcriber-home/transcriber
uv init --lib --name transcriber --python 3.13
```

**Step 2: Verify project structure created**

```bash
ls -la pyproject.toml src/
```
Expected: `pyproject.toml` exists, `src/transcriber/` directory created

**Step 3: Update pyproject.toml with full configuration**

Replace contents of `pyproject.toml` with:

```toml
[project]
name = "transcriber"
version = "0.1.0"
description = "Voice capture and processing system for DJI audio recordings"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.15.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
stt-parakeet = ["parakeet-mlx>=0.1.0"]
stt-whisper = ["openai-whisper>=20231117"]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.8.0",
    "ruff>=0.4.0",
]

[project.scripts]
transcriber = "transcriber.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/transcriber"]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.13"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"
```

**Step 4: Create src/transcriber/__init__.py**

```python
"""Transcriber - Voice capture and processing system."""

__version__ = "0.1.0"
```

**Step 5: Create src/transcriber/py.typed**

```bash
touch src/transcriber/py.typed
```

**Step 6: Install dependencies**

```bash
uv sync --all-extras
```
Expected: Dependencies installed successfully

**Step 7: Verify universal invocation works**

```bash
uv run transcriber --help
```
Expected: Error (cli not yet implemented), but confirms uv run works

**Step 8: Commit**

```bash
git add pyproject.toml src/ uv.lock
git commit -m "feat: initialize Python project with uv"
```

---

### Task 2: Create Configuration Module

**Files:**
- Create: `src/transcriber/config.py`
- Create: `tests/test_config.py`
- Create: `config/default.toml`

**Step 1: Write the failing test**

Create `tests/__init__.py`:
```python
"""Transcriber test suite."""
```

Create `tests/test_config.py`:
```python
"""Tests for configuration module."""

import pytest
from pathlib import Path
from transcriber.config import TranscriberConfig, load_config


def test_default_config_has_required_paths():
    """Default config should have all required directory paths."""
    config = TranscriberConfig()
    assert config.paths.audio_unprocessed.endswith("audio-unprocessed")
    assert config.paths.audio_processed.endswith("audio-processed")
    assert config.paths.text_unprocessed.endswith("text-unprocessed")
    assert config.paths.text_processed.endswith("text-processed")
    assert config.paths.transcripts.endswith("transcripts")


def test_default_config_has_dji_source():
    """Default config should have DJI source path."""
    config = TranscriberConfig()
    assert config.paths.dji_source == "/Volumes/DJI_MIC2"


def test_default_stt_provider_is_parakeet():
    """Default STT provider should be parakeet."""
    config = TranscriberConfig()
    assert config.stt.provider == "parakeet"


def test_default_llm_model():
    """Default LLM model should be transcriber:latest."""
    config = TranscriberConfig()
    assert config.llm.model == "transcriber:latest"


def test_load_config_returns_defaults_when_no_file(tmp_path):
    """load_config should return defaults when config file doesn't exist."""
    config = load_config(config_path=tmp_path / "nonexistent.toml")
    assert isinstance(config, TranscriberConfig)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'transcriber.config'"

**Step 3: Write minimal implementation**

Create `src/transcriber/config.py`:
```python
"""Configuration management for transcriber."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class PathsConfig(BaseModel):
    """Directory paths configuration."""

    base: str = "~/Resources/Transcripts"
    dji_source: str = "/Volumes/DJI_MIC2"

    @property
    def audio_unprocessed(self) -> str:
        return str(Path(self.base).expanduser() / "audio-unprocessed")

    @property
    def audio_processed(self) -> str:
        return str(Path(self.base).expanduser() / "audio-processed")

    @property
    def text_unprocessed(self) -> str:
        return str(Path(self.base).expanduser() / "text-unprocessed")

    @property
    def text_processed(self) -> str:
        return str(Path(self.base).expanduser() / "text-processed")

    @property
    def transcripts(self) -> str:
        return str(Path(self.base).expanduser() / "transcripts")


class STTConfig(BaseModel):
    """Speech-to-text configuration."""

    provider: Literal["parakeet", "whisper"] = "parakeet"
    model: str | None = None  # Provider-specific model name


class LLMConfig(BaseModel):
    """LLM processing configuration."""

    provider: Literal["ollama", "claude"] = "ollama"
    model: str = "transcriber:latest"


class TranscriberConfig(BaseModel):
    """Main configuration for transcriber."""

    paths: PathsConfig = PathsConfig()
    stt: STTConfig = STTConfig()
    llm: LLMConfig = LLMConfig()


def load_config(config_path: Path | None = None) -> TranscriberConfig:
    """Load configuration from TOML file, falling back to defaults.

    Args:
        config_path: Path to TOML config file. If None, uses default locations.

    Returns:
        TranscriberConfig with loaded or default values.
    """
    import tomllib

    # Default config locations (checked in order)
    if config_path is None:
        candidates = [
            Path.cwd() / "transcriber.toml",
            Path.home() / ".config" / "transcriber" / "config.toml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break

    if config_path is not None and config_path.exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return TranscriberConfig.model_validate(data)

    return TranscriberConfig()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_config.py -v
```
Expected: All 5 tests PASS

**Step 5: Create default config file**

Create `config/default.toml`:
```toml
# Transcriber default configuration
# Copy to ~/.config/transcriber/config.toml to customize

[paths]
base = "~/Resources/Transcripts"
dji_source = "/Volumes/DJI_MIC2"

[stt]
provider = "parakeet"
# model = "custom-model"  # Optional: provider-specific model

[llm]
provider = "ollama"
model = "transcriber:latest"
```

**Step 6: Commit**

```bash
git add src/transcriber/config.py tests/ config/
git commit -m "feat: add configuration module with Pydantic models"
```

---

### Task 3: Create CLI Skeleton

**Files:**
- Create: `src/transcriber/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

Create `tests/test_cli.py`:
```python
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
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_cli.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'transcriber.cli'"

**Step 3: Write minimal implementation**

Create `src/transcriber/cli.py`:
```python
"""Command-line interface for transcriber."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from transcriber import __version__
from transcriber.config import TranscriberConfig, load_config

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
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Transcriber - Voice capture and processing system."""
    pass


@app.command()
def process(
    config_file: Annotated[
        Optional[str],
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
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_cli.py -v
```
Expected: All 3 tests PASS

**Step 5: Verify universal invocation**

```bash
uv run transcriber --version
uv run transcriber --help
uv run transcriber process --help
```
Expected: All commands work without venv activation

**Step 6: Commit**

```bash
git add src/transcriber/cli.py tests/test_cli.py
git commit -m "feat: add CLI skeleton with Typer"
```

---

## Phase 2: Core Pipeline

### Task 4: Audio Import Module

**Files:**
- Create: `src/transcriber/audio.py`
- Create: `tests/test_audio.py`

**Step 1: Write the failing tests**

Create `tests/test_audio.py`:
```python
"""Tests for audio import module."""

import pytest
from pathlib import Path
from transcriber.audio import parse_dji_filename, rename_dji_file, import_dji_audio


def test_parse_dji_filename_valid():
    """Should parse valid DJI filename into components."""
    result = parse_dji_filename("DJI_01_20250702_175446.WAV")
    assert result is not None
    assert result.year == "2025"
    assert result.month == "07"
    assert result.day == "02"
    assert result.hour == "17"
    assert result.minute == "54"
    assert result.second == "46"


def test_parse_dji_filename_invalid():
    """Should return None for non-DJI filename."""
    result = parse_dji_filename("random_file.wav")
    assert result is None


def test_rename_dji_file():
    """Should convert DJI filename to ISO format."""
    result = rename_dji_file("DJI_01_20250702_175446.WAV")
    assert result == "2025-07-02-17:54:46.WAV"


def test_rename_dji_file_invalid_returns_none():
    """Should return None for non-DJI filename."""
    result = rename_dji_file("random_file.wav")
    assert result is None


def test_import_dji_audio_creates_dest_dir(tmp_path):
    """Should create destination directory if it doesn't exist."""
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest" / "audio-unprocessed"

    # Create a DJI audio directory with a file
    dji_dir = source / "DJI_Audio_001"
    dji_dir.mkdir()
    (dji_dir / "DJI_01_20250702_175446.WAV").write_bytes(b"fake audio")

    result = import_dji_audio(source_base=source, dest_dir=dest)

    assert dest.exists()
    assert result.total_found == 1
    assert result.processed == 1


def test_import_dji_audio_renames_correctly(tmp_path):
    """Should rename files to ISO format."""
    source = tmp_path / "source"
    dest = tmp_path / "dest"

    dji_dir = source / "DJI_Audio_001"
    dji_dir.mkdir(parents=True)
    (dji_dir / "DJI_01_20250702_175446.WAV").write_bytes(b"fake audio")

    import_dji_audio(source_base=source, dest_dir=dest)

    expected_file = dest / "2025-07-02-17:54:46.WAV"
    assert expected_file.exists()


def test_import_dji_audio_skips_existing(tmp_path):
    """Should skip files that already exist in destination."""
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    dest.mkdir(parents=True)

    dji_dir = source / "DJI_Audio_001"
    dji_dir.mkdir(parents=True)
    (dji_dir / "DJI_01_20250702_175446.WAV").write_bytes(b"fake audio")

    # Pre-create destination file
    (dest / "2025-07-02-17:54:46.WAV").write_bytes(b"existing")

    result = import_dji_audio(source_base=source, dest_dir=dest)

    assert result.skipped == 1
    assert result.processed == 0
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_audio.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'transcriber.audio'"

**Step 3: Write minimal implementation**

Create `src/transcriber/audio.py`:
```python
"""Audio file import and management."""

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DJIFileParts:
    """Parsed components of a DJI filename."""

    year: str
    month: str
    day: str
    hour: str
    minute: str
    second: str


@dataclass
class ImportResult:
    """Result of audio import operation."""

    total_found: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0


# Pattern: DJI_XX_YYYYMMDD_HHMMSS.WAV
DJI_PATTERN = re.compile(r"^DJI_\d+_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.WAV$")


def parse_dji_filename(filename: str) -> DJIFileParts | None:
    """Parse a DJI filename into its date/time components.

    Args:
        filename: The filename to parse (e.g., "DJI_01_20250702_175446.WAV")

    Returns:
        DJIFileParts if valid DJI filename, None otherwise.
    """
    match = DJI_PATTERN.match(filename)
    if not match:
        return None

    return DJIFileParts(
        year=match.group(1),
        month=match.group(2),
        day=match.group(3),
        hour=match.group(4),
        minute=match.group(5),
        second=match.group(6),
    )


def rename_dji_file(filename: str) -> str | None:
    """Convert DJI filename to ISO timestamp format.

    Args:
        filename: DJI filename (e.g., "DJI_01_20250702_175446.WAV")

    Returns:
        ISO format filename (e.g., "2025-07-02-17:54:46.WAV") or None if invalid.
    """
    parts = parse_dji_filename(filename)
    if not parts:
        return None

    return f"{parts.year}-{parts.month}-{parts.day}-{parts.hour}:{parts.minute}:{parts.second}.WAV"


def import_dji_audio(
    source_base: Path,
    dest_dir: Path,
    move: bool = True,
) -> ImportResult:
    """Import and rename DJI audio files.

    Scans source_base for DJI_Audio_* directories and imports .WAV files
    to dest_dir with ISO timestamp filenames.

    Args:
        source_base: Base directory to scan (e.g., /Volumes/DJI_MIC2)
        dest_dir: Destination directory for renamed files
        move: If True, move files. If False, copy.

    Returns:
        ImportResult with counts of processed files.
    """
    result = ImportResult()

    # Create destination if needed
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Find all DJI_Audio_* directories
    if not source_base.exists():
        return result

    audio_dirs = sorted(source_base.glob("DJI_Audio_*"))

    for audio_dir in audio_dirs:
        if not audio_dir.is_dir():
            continue

        for wav_file in audio_dir.glob("*.WAV"):
            result.total_found += 1

            new_name = rename_dji_file(wav_file.name)
            if new_name is None:
                result.skipped += 1
                continue

            dest_file = dest_dir / new_name

            if dest_file.exists():
                result.skipped += 1
                continue

            try:
                if move:
                    shutil.move(str(wav_file), str(dest_file))
                else:
                    shutil.copy2(str(wav_file), str(dest_file))
                result.processed += 1
            except OSError:
                result.failed += 1

    return result
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_audio.py -v
```
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add src/transcriber/audio.py tests/test_audio.py
git commit -m "feat: add audio import module with DJI file handling"
```

---

### Task 5: Speech-to-Text Module

**Files:**
- Create: `src/transcriber/stt.py`
- Create: `tests/test_stt.py`

**Step 1: Write the failing tests**

Create `tests/test_stt.py`:
```python
"""Tests for speech-to-text module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from transcriber.stt import (
    STTProvider,
    get_stt_provider,
    ParakeetProvider,
    TranscribeResult,
)


def test_get_stt_provider_parakeet():
    """Should return ParakeetProvider for 'parakeet'."""
    provider = get_stt_provider("parakeet")
    assert isinstance(provider, ParakeetProvider)


def test_get_stt_provider_unknown_raises():
    """Should raise ValueError for unknown provider."""
    with pytest.raises(ValueError, match="Unknown STT provider"):
        get_stt_provider("unknown_provider")


def test_parakeet_provider_check_available():
    """ParakeetProvider should check if parakeet-mlx is installed."""
    provider = ParakeetProvider()
    # Just verify the method exists and returns bool
    result = provider.is_available()
    assert isinstance(result, bool)


def test_transcribe_result_dataclass():
    """TranscribeResult should hold transcription data."""
    result = TranscribeResult(
        audio_file=Path("/test/audio.wav"),
        text_file=Path("/test/audio.txt"),
        success=True,
    )
    assert result.success
    assert result.error is None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_stt.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'transcriber.stt'"

**Step 3: Write minimal implementation**

Create `src/transcriber/stt.py`:
```python
"""Speech-to-text providers."""

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranscribeResult:
    """Result of a transcription operation."""

    audio_file: Path
    text_file: Path | None
    success: bool
    error: str | None = None


class STTProvider(ABC):
    """Abstract base class for speech-to-text providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available on the system."""
        ...

    @abstractmethod
    def transcribe(self, audio_file: Path, output_dir: Path) -> TranscribeResult:
        """Transcribe an audio file.

        Args:
            audio_file: Path to audio file
            output_dir: Directory for output text file

        Returns:
            TranscribeResult with outcome
        """
        ...


class ParakeetProvider(STTProvider):
    """Speech-to-text using parakeet-mlx."""

    def is_available(self) -> bool:
        """Check if parakeet-mlx is installed."""
        return shutil.which("parakeet-mlx") is not None

    def transcribe(self, audio_file: Path, output_dir: Path) -> TranscribeResult:
        """Transcribe using parakeet-mlx.

        Args:
            audio_file: Path to audio file
            output_dir: Directory for output text file

        Returns:
            TranscribeResult with outcome
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                [
                    "parakeet-mlx",
                    str(audio_file),
                    "--output-format",
                    "txt",
                    "--output-dir",
                    str(output_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # parakeet-mlx creates a .txt file with same name as input
            text_file = output_dir / f"{audio_file.stem}.txt"

            return TranscribeResult(
                audio_file=audio_file,
                text_file=text_file if text_file.exists() else None,
                success=text_file.exists(),
                error=None if text_file.exists() else "Output file not created",
            )

        except subprocess.CalledProcessError as e:
            return TranscribeResult(
                audio_file=audio_file,
                text_file=None,
                success=False,
                error=f"parakeet-mlx failed: {e.stderr}",
            )
        except FileNotFoundError:
            return TranscribeResult(
                audio_file=audio_file,
                text_file=None,
                success=False,
                error="parakeet-mlx not found",
            )


def get_stt_provider(provider_name: str, model: str | None = None) -> STTProvider:
    """Get an STT provider by name.

    Args:
        provider_name: Name of provider ("parakeet", "whisper")
        model: Optional model name for the provider

    Returns:
        STTProvider instance

    Raises:
        ValueError: If provider is unknown
    """
    providers: dict[str, type[STTProvider]] = {
        "parakeet": ParakeetProvider,
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown STT provider: {provider_name}")

    return providers[provider_name]()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_stt.py -v
```
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/transcriber/stt.py tests/test_stt.py
git commit -m "feat: add speech-to-text module with parakeet provider"
```

---

### Task 6: LLM Processing Module

**Files:**
- Create: `src/transcriber/llm.py`
- Create: `tests/test_llm.py`

**Step 1: Write the failing tests**

Create `tests/test_llm.py`:
```python
"""Tests for LLM processing module."""

import pytest
from pathlib import Path
from unittest.mock import patch
from transcriber.llm import (
    LLMProvider,
    get_llm_provider,
    OllamaProvider,
    ProcessResult,
)


def test_get_llm_provider_ollama():
    """Should return OllamaProvider for 'ollama'."""
    provider = get_llm_provider("ollama", model="transcriber:latest")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "transcriber:latest"


def test_get_llm_provider_unknown_raises():
    """Should raise ValueError for unknown provider."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_provider("unknown_provider", model="test")


def test_ollama_provider_check_available():
    """OllamaProvider should check if ollama is installed."""
    provider = OllamaProvider(model="test")
    result = provider.is_available()
    assert isinstance(result, bool)


def test_process_result_dataclass():
    """ProcessResult should hold processing data."""
    result = ProcessResult(
        input_file=Path("/test/input.txt"),
        output_file=Path("/test/output.md"),
        success=True,
    )
    assert result.success
    assert result.error is None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_llm.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'transcriber.llm'"

**Step 3: Write minimal implementation**

Create `src/transcriber/llm.py`:
```python
"""LLM processing providers."""

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessResult:
    """Result of LLM processing operation."""

    input_file: Path
    output_file: Path | None
    success: bool
    error: str | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available on the system."""
        ...

    @abstractmethod
    def process(self, input_file: Path, output_file: Path) -> ProcessResult:
        """Process a text file through the LLM.

        Args:
            input_file: Path to input text file
            output_file: Path for output file

        Returns:
            ProcessResult with outcome
        """
        ...


class OllamaProvider(LLMProvider):
    """LLM processing using Ollama."""

    def __init__(self, model: str) -> None:
        self.model = model

    def is_available(self) -> bool:
        """Check if ollama is installed."""
        return shutil.which("ollama") is not None

    def process(self, input_file: Path, output_file: Path) -> ProcessResult:
        """Process text through ollama model.

        Args:
            input_file: Path to input text file
            output_file: Path for output markdown file

        Returns:
            ProcessResult with outcome
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Read input file
            input_text = input_file.read_text()

            # Run ollama
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=input_text,
                capture_output=True,
                text=True,
                check=True,
            )

            # Write output
            output_file.write_text(result.stdout)

            return ProcessResult(
                input_file=input_file,
                output_file=output_file,
                success=True,
            )

        except subprocess.CalledProcessError as e:
            return ProcessResult(
                input_file=input_file,
                output_file=None,
                success=False,
                error=f"ollama failed: {e.stderr}",
            )
        except FileNotFoundError:
            return ProcessResult(
                input_file=input_file,
                output_file=None,
                success=False,
                error="ollama not found",
            )


def get_llm_provider(provider_name: str, model: str) -> LLMProvider:
    """Get an LLM provider by name.

    Args:
        provider_name: Name of provider ("ollama", "claude")
        model: Model name for the provider

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider_name == "ollama":
        return OllamaProvider(model=model)

    raise ValueError(f"Unknown LLM provider: {provider_name}")
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_llm.py -v
```
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/transcriber/llm.py tests/test_llm.py
git commit -m "feat: add LLM processing module with ollama provider"
```

---

### Task 7: Pipeline Orchestration

**Files:**
- Create: `src/transcriber/pipeline.py`
- Create: `tests/test_pipeline.py`
- Modify: `src/transcriber/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_pipeline.py`:
```python
"""Tests for pipeline orchestration."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from transcriber.pipeline import Pipeline, PipelineResult
from transcriber.config import TranscriberConfig


def test_pipeline_init_with_config():
    """Pipeline should initialize with config."""
    config = TranscriberConfig()
    pipeline = Pipeline(config)
    assert pipeline.config == config


def test_pipeline_result_summary():
    """PipelineResult should provide summary."""
    result = PipelineResult(
        audio_imported=5,
        audio_skipped=1,
        transcribed=4,
        transcribe_failed=1,
        processed=3,
        process_failed=1,
    )
    assert result.audio_imported == 5
    assert result.total_successful == 3


def test_pipeline_run_returns_result():
    """Pipeline.run should return PipelineResult."""
    config = TranscriberConfig()
    pipeline = Pipeline(config)

    with patch.object(pipeline, '_import_audio') as mock_import:
        with patch.object(pipeline, '_transcribe_audio') as mock_transcribe:
            with patch.object(pipeline, '_process_transcripts') as mock_process:
                mock_import.return_value = (0, 0, 0)
                mock_transcribe.return_value = (0, 0)
                mock_process.return_value = (0, 0)

                result = pipeline.run()

    assert isinstance(result, PipelineResult)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_pipeline.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'transcriber.pipeline'"

**Step 3: Write minimal implementation**

Create `src/transcriber/pipeline.py`:
```python
"""Pipeline orchestration for transcriber."""

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from transcriber.audio import import_dji_audio
from transcriber.config import TranscriberConfig
from transcriber.llm import get_llm_provider
from transcriber.stt import get_stt_provider


@dataclass
class PipelineResult:
    """Result of running the full pipeline."""

    audio_imported: int = 0
    audio_skipped: int = 0
    audio_failed: int = 0
    transcribed: int = 0
    transcribe_failed: int = 0
    processed: int = 0
    process_failed: int = 0

    @property
    def total_successful(self) -> int:
        """Count of fully processed files."""
        return self.processed


class Pipeline:
    """Orchestrates the full transcription pipeline."""

    def __init__(self, config: TranscriberConfig) -> None:
        self.config = config
        self.console = Console()

    def run(self, skip_import: bool = False) -> PipelineResult:
        """Run the full pipeline.

        Args:
            skip_import: If True, skip audio import step

        Returns:
            PipelineResult with processing counts
        """
        result = PipelineResult()

        # Step 1: Import audio
        if not skip_import:
            imported, skipped, failed = self._import_audio()
            result.audio_imported = imported
            result.audio_skipped = skipped
            result.audio_failed = failed

        # Step 2: Transcribe
        transcribed, t_failed = self._transcribe_audio()
        result.transcribed = transcribed
        result.transcribe_failed = t_failed

        # Step 3: Process through LLM
        processed, p_failed = self._process_transcripts()
        result.processed = processed
        result.process_failed = p_failed

        return result

    def _import_audio(self) -> tuple[int, int, int]:
        """Import audio from DJI device."""
        self.console.print("\n[bold blue]Step 1: Importing audio files...[/bold blue]")

        source = Path(self.config.paths.dji_source)
        dest = Path(self.config.paths.audio_unprocessed)

        if not source.exists():
            self.console.print(f"[yellow]DJI device not found at {source}[/yellow]")
            return 0, 0, 0

        result = import_dji_audio(source_base=source, dest_dir=dest)

        self.console.print(f"  Imported: {result.processed}")
        self.console.print(f"  Skipped: {result.skipped}")
        self.console.print(f"  Failed: {result.failed}")

        return result.processed, result.skipped, result.failed

    def _transcribe_audio(self) -> tuple[int, int]:
        """Transcribe audio files."""
        self.console.print("\n[bold blue]Step 2: Transcribing audio...[/bold blue]")

        audio_dir = Path(self.config.paths.audio_unprocessed)
        processed_dir = Path(self.config.paths.audio_processed)
        text_dir = Path(self.config.paths.text_unprocessed)

        processed_dir.mkdir(parents=True, exist_ok=True)

        if not audio_dir.exists():
            self.console.print("[yellow]No audio directory found[/yellow]")
            return 0, 0

        wav_files = list(audio_dir.glob("*.WAV"))
        if not wav_files:
            self.console.print("[yellow]No WAV files to transcribe[/yellow]")
            return 0, 0

        provider = get_stt_provider(self.config.stt.provider, self.config.stt.model)

        if not provider.is_available():
            self.console.print(f"[red]STT provider '{self.config.stt.provider}' not available[/red]")
            return 0, len(wav_files)

        success_count = 0
        fail_count = 0

        for wav_file in wav_files:
            self.console.print(f"  Processing: {wav_file.name}")

            result = provider.transcribe(wav_file, text_dir)

            if result.success:
                # Move processed audio
                import shutil
                shutil.move(str(wav_file), str(processed_dir / wav_file.name))
                self.console.print(f"    [green]✓ Transcribed[/green]")
                success_count += 1
            else:
                self.console.print(f"    [red]✗ Failed: {result.error}[/red]")
                fail_count += 1

        return success_count, fail_count

    def _process_transcripts(self) -> tuple[int, int]:
        """Process transcripts through LLM."""
        self.console.print("\n[bold blue]Step 3: Processing transcripts...[/bold blue]")

        text_dir = Path(self.config.paths.text_unprocessed)
        processed_dir = Path(self.config.paths.text_processed)
        output_dir = Path(self.config.paths.transcripts)

        processed_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not text_dir.exists():
            self.console.print("[yellow]No text directory found[/yellow]")
            return 0, 0

        txt_files = list(text_dir.glob("*.txt"))
        if not txt_files:
            self.console.print("[yellow]No text files to process[/yellow]")
            return 0, 0

        provider = get_llm_provider(self.config.llm.provider, self.config.llm.model)

        if not provider.is_available():
            self.console.print(f"[red]LLM provider '{self.config.llm.provider}' not available[/red]")
            return 0, len(txt_files)

        success_count = 0
        fail_count = 0

        for txt_file in txt_files:
            self.console.print(f"  Processing: {txt_file.name}")

            base_name = txt_file.stem
            output_file = output_dir / f"transcript-{base_name}.md"

            result = provider.process(txt_file, output_file)

            if result.success:
                # Move processed text
                import shutil
                shutil.move(str(txt_file), str(processed_dir / txt_file.name))
                self.console.print(f"    [green]✓ Generated: {output_file.name}[/green]")
                success_count += 1
            else:
                self.console.print(f"    [red]✗ Failed: {result.error}[/red]")
                fail_count += 1

        return success_count, fail_count
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_pipeline.py -v
```
Expected: All 3 tests PASS

**Step 5: Wire pipeline to CLI**

Update `src/transcriber/cli.py`, replace the `process` command:

```python
@app.command()
def process(
    config_file: Annotated[
        Optional[str],
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
    skip_import: Annotated[
        bool,
        typer.Option("--skip-import", help="Skip audio import step"),
    ] = False,
) -> None:
    """Run the full transcription pipeline.

    Imports audio from DJI device, transcribes, and processes through LLM.
    """
    from pathlib import Path
    from transcriber.pipeline import Pipeline

    config_path = Path(config_file) if config_file else None
    config = load_config(config_path)

    console.print("[bold blue]Starting transcription pipeline...[/bold blue]")
    console.print(f"  DJI Source: {config.paths.dji_source}")
    console.print(f"  Output: {config.paths.base}")
    console.print(f"  STT Provider: {config.stt.provider}")
    console.print(f"  LLM Model: {config.llm.model}")

    pipeline = Pipeline(config)
    result = pipeline.run(skip_import=skip_import)

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print(f"  Audio imported: {result.audio_imported}")
    console.print(f"  Transcribed: {result.transcribed}")
    console.print(f"  Processed: {result.processed}")

    if result.transcribe_failed or result.process_failed:
        console.print(f"  [yellow]Failures: {result.transcribe_failed + result.process_failed}[/yellow]")
```

**Step 6: Run all tests**

```bash
uv run pytest -v
```
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/transcriber/pipeline.py src/transcriber/cli.py tests/test_pipeline.py
git commit -m "feat: add pipeline orchestration and wire to CLI"
```

---

## Phase 3: Integration Testing

### Task 8: End-to-End Test with Mocks

**Files:**
- Create: `tests/test_e2e.py`

**Step 1: Write the e2e test**

Create `tests/test_e2e.py`:
```python
"""End-to-end tests for transcriber pipeline."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from transcriber.cli import app
from transcriber.config import TranscriberConfig

runner = CliRunner()


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directory structure."""
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


def test_full_pipeline_with_mocked_externals(temp_dirs, tmp_path):
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

    # Mock the external commands
    def mock_stt_run(*args, **kwargs):
        # Simulate parakeet-mlx creating output file
        if "parakeet-mlx" in args[0]:
            output_dir = Path(args[0][args[0].index("--output-dir") + 1])
            audio_file = Path(args[0][1])
            output_file = output_dir / f"{audio_file.stem}.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("This is transcribed text.")
        return MagicMock(returncode=0, stdout="", stderr="")

    def mock_llm_run(*args, **kwargs):
        return MagicMock(returncode=0, stdout="# Processed Transcript\n\nThis is processed.", stderr="")

    with patch("shutil.which", return_value="/usr/bin/mock"):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = mock_stt_run

            # For LLM, we need different behavior
            original_side_effect = mock_run.side_effect
            def combined_mock(*args, **kwargs):
                if args[0][0] == "ollama":
                    return mock_llm_run(*args, **kwargs)
                return mock_stt_run(*args, **kwargs)

            mock_run.side_effect = combined_mock

            result = runner.invoke(app, ["process", "--config", str(config_file)])

    # Verify pipeline ran
    assert result.exit_code == 0 or "not found" not in result.output.lower()
```

**Step 2: Run e2e test**

```bash
uv run pytest tests/test_e2e.py -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add end-to-end test with mocked externals"
```

---

### Task 9: Final Verification and Cleanup

**Files:**
- Verify: All modules
- Update: `README.md` (brief note about Python version)

**Step 1: Run full test suite**

```bash
uv run pytest -v --cov=transcriber --cov-report=term-missing
```
Expected: All tests pass, reasonable coverage

**Step 2: Run type checker**

```bash
uv run mypy src/transcriber/
```
Expected: No errors (or minimal, acceptable ones)

**Step 3: Run linter**

```bash
uv run ruff check src/ tests/
```
Expected: No errors

**Step 4: Test universal invocation**

```bash
# These should all work without activating any venv
uv run transcriber --version
uv run transcriber --help
uv run transcriber process --help
```

**Step 5: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix linting and type errors"
```

**Step 6: Final commit summary**

```bash
git log --oneline -10
```

---

## Future Extensions (Not in This Plan)

These are documented for future implementation:

### Term Correction (`dictionaries/` or `synonyms.md`)
- YAML files mapping misheard terms to correct spellings
- Loaded from `~/.config/transcriber/dictionaries/` or project-local
- Applied after STT, before LLM processing

### Classification (`TOPIC.md` files)
- Topic definition files with keywords/patterns
- Auto-classify transcripts into `projects/<topic>/`
- Fallback to `misc/` when no match

### Templates
- Jinja2 templates for different output formats
- `--template blog`, `--template summary`, etc.

---

## Summary

| Task | Description | Est. Time |
|------|-------------|-----------|
| 1 | Initialize uv project | 10 min |
| 2 | Configuration module | 15 min |
| 3 | CLI skeleton | 10 min |
| 4 | Audio import module | 15 min |
| 5 | Speech-to-text module | 15 min |
| 6 | LLM processing module | 15 min |
| 7 | Pipeline orchestration | 20 min |
| 8 | E2E test | 15 min |
| 9 | Final verification | 10 min |

**Total estimated time:** ~2 hours

After completing this plan, you'll have a working Python transcriber that:
- Matches the bash script's functionality
- Uses `uv run transcriber` (no venv activation)
- Is configurable via TOML
- Has pluggable STT providers (parakeet now, whisper later)
- Has comprehensive tests
- Is ready for future extension (dictionaries, classification, templates)
