"""Tests for pipeline orchestration."""

from unittest.mock import patch

from transcriber.config import TranscriberConfig
from transcriber.pipeline import Pipeline, PipelineResult


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


def test_pipeline_run_with_skip_import():
    """Pipeline.run should respect skip_import flag."""
    config = TranscriberConfig()
    pipeline = Pipeline(config)

    with patch.object(pipeline, '_import_audio') as mock_import:
        with patch.object(pipeline, '_transcribe_audio') as mock_transcribe:
            with patch.object(pipeline, '_process_transcripts') as mock_process:
                mock_import.return_value = (0, 0, 0)
                mock_transcribe.return_value = (0, 0)
                mock_process.return_value = (0, 0)

                result = pipeline.run(skip_import=True)

    mock_import.assert_not_called()
    assert isinstance(result, PipelineResult)


def test_pipeline_result_total_successful():
    """PipelineResult.total_successful should equal processed count."""
    result = PipelineResult(
        audio_imported=10,
        audio_skipped=2,
        transcribed=8,
        transcribe_failed=0,
        processed=7,
        process_failed=1,
    )
    # total_successful is the final count of fully processed transcripts
    assert result.total_successful == 7


def test_pipeline_result_default_values():
    """PipelineResult should have sensible defaults."""
    result = PipelineResult()
    assert result.audio_imported == 0
    assert result.audio_skipped == 0
    assert result.transcribed == 0
    assert result.transcribe_failed == 0
    assert result.processed == 0
    assert result.process_failed == 0
    assert result.total_successful == 0
