"""Tests for LLM processing module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_ollama_classify_sends_prompt() -> None:
    """classify() should send the prompt to ollama and return result."""
    provider = OllamaProvider(model="transcriber:latest")

    mock_result = MagicMock()
    mock_result.stdout = '{"intents": [], "suggested_tags": []}'
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch("shutil.which", return_value="/usr/bin/ollama"):
            result = provider.classify("Analyze this text")

    assert result.stdout == '{"intents": [], "suggested_tags": []}'
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["ollama", "run", "transcriber:latest"]
    assert call_args[1]["input"] == "Analyze this text"


def test_ollama_process_strips_ansi_escapes(tmp_path) -> None:
    """process() should strip ANSI escape sequences from Ollama output."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("Raw transcript text.")
    output_file = tmp_path / "output.md"

    ansi_output = "The desired outcomes\x1b[1D\x1b[K\nare completely different\x1b[3D\x1b[K"
    expected_clean = "The desired outcomes\nare completely different"

    mock_result = MagicMock()
    mock_result.stdout = ansi_output
    mock_result.returncode = 0

    provider = OllamaProvider(model="test-model")

    with patch("subprocess.run", return_value=mock_result):
        result = provider.process(input_file, output_file)

    assert result.success
    content = output_file.read_text()
    assert "\x1b" not in content
    assert content == expected_clean


def test_ollama_classify_strips_ansi_escapes() -> None:
    """classify() should strip ANSI escape sequences from Ollama output."""
    ansi_output = '{"intent": "todo"}\x1b[1D\x1b[K'

    mock_result = MagicMock()
    mock_result.stdout = ansi_output
    mock_result.returncode = 0

    provider = OllamaProvider(model="test-model")

    with patch("subprocess.run", return_value=mock_result):
        result = provider.classify("Analyze this text")

    assert "\x1b" not in result.stdout
    assert result.stdout == '{"intent": "todo"}'
