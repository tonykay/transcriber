"""Tests for LLM processing module."""

from pathlib import Path

import pytest

from transcriber.llm import (
    OllamaProvider,
    ProcessResult,
    get_llm_provider,
)


def test_get_llm_provider_ollama() -> None:
    """Should return OllamaProvider for 'ollama'."""
    provider = get_llm_provider("ollama", model="transcriber:latest")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "transcriber:latest"


def test_get_llm_provider_unknown_raises() -> None:
    """Should raise ValueError for unknown provider."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_provider("unknown_provider", model="test")


def test_ollama_provider_check_available() -> None:
    """OllamaProvider should check if ollama is installed."""
    provider = OllamaProvider(model="test")
    result = provider.is_available()
    assert isinstance(result, bool)


def test_process_result_dataclass() -> None:
    """ProcessResult should hold processing data."""
    result = ProcessResult(
        input_file=Path("/test/input.txt"),
        output_file=Path("/test/output.md"),
        success=True,
    )
    assert result.success
    assert result.error is None
