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
        ISO format filename (e.g., "2025-07-02-17-54-46.WAV") or None if invalid.
    """
    parts = parse_dji_filename(filename)
    if not parts:
        return None

    return f"{parts.year}-{parts.month}-{parts.day}-{parts.hour}-{parts.minute}-{parts.second}.WAV"


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
