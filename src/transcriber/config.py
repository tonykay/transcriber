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
