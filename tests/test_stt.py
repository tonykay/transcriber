"""Tests for speech-to-text module."""

from pathlib import Path

import pytest

from transcriber.stt import (
    ParakeetProvider,
    TranscribeResult,
    get_stt_provider,
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
