"""Tests for audio import module."""

from pathlib import Path

from transcriber.audio import import_dji_audio, parse_dji_filename, rename_dji_file


def test_parse_dji_filename_valid() -> None:
    """Should parse valid DJI filename into components."""
    result = parse_dji_filename("DJI_01_20250702_175446.WAV")
    assert result is not None
    assert result.year == "2025"
    assert result.month == "07"
    assert result.day == "02"
    assert result.hour == "17"
    assert result.minute == "54"
    assert result.second == "46"


def test_parse_dji_filename_invalid() -> None:
    """Should return None for non-DJI filename."""
    result = parse_dji_filename("random_file.wav")
    assert result is None


def test_rename_dji_file() -> None:
    """Should convert DJI filename to ISO format."""
    result = rename_dji_file("DJI_01_20250702_175446.WAV")
    assert result == "2025-07-02-17:54:46.WAV"


def test_rename_dji_file_invalid_returns_none() -> None:
    """Should return None for non-DJI filename."""
    result = rename_dji_file("random_file.wav")
    assert result is None


def test_import_dji_audio_creates_dest_dir(tmp_path: Path) -> None:
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


def test_import_dji_audio_renames_correctly(tmp_path: Path) -> None:
    """Should rename files to ISO format."""
    source = tmp_path / "source"
    dest = tmp_path / "dest"

    dji_dir = source / "DJI_Audio_001"
    dji_dir.mkdir(parents=True)
    (dji_dir / "DJI_01_20250702_175446.WAV").write_bytes(b"fake audio")

    import_dji_audio(source_base=source, dest_dir=dest)

    expected_file = dest / "2025-07-02-17:54:46.WAV"
    assert expected_file.exists()


def test_import_dji_audio_skips_existing(tmp_path: Path) -> None:
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
