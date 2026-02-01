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
            subprocess.run(
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
