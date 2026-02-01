"""Tests for configuration module."""

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
