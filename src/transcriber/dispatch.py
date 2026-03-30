"""Output dispatch for routing intents to files."""

import re
from datetime import datetime
from pathlib import Path

from transcriber.frontmatter import format_append_entry, generate_frontmatter
from transcriber.router import ExtractedIntent


def append_to_file(
    target: Path,
    intent: ExtractedIntent,
    date: datetime,
    source: str,
    source_transcript: str | None = None,
) -> None:
    """Append an extracted intent entry to a capture file.

    Creates the file if it doesn't exist. Appends a formatted
    checklist entry with metadata.

    Args:
        target: Path to the append target file (e.g. todos.md).
        intent: The extracted intent to append.
        date: Timestamp of the recording.
        source: Source audio filename.
        source_transcript: Full transcript filename (for embedded intents).
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    transcript_ref = source_transcript if intent.position == "embedded" else None

    entry = format_append_entry(
        content=intent.content,
        date=date,
        source=source,
        tags=intent.tags,
        assigned=intent.person,
        source_transcript=transcript_ref,
    )

    with open(target, "a") as f:
        f.write(entry + "\n")


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].rstrip("-")


def write_intent_file(
    target_dir: Path,
    intent: ExtractedIntent,
    date: datetime,
    source: str,
    full_text: str,
    project: str | None = None,
) -> Path:
    """Write an intent as an individual markdown file with frontmatter.

    Args:
        target_dir: Directory to write the file in.
        intent: The extracted intent.
        date: Timestamp of the recording.
        source: Source audio filename.
        full_text: Full transcript text for the file body.
        project: Classified project name.

    Returns:
        Path to the created file.
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(intent.content[:60])
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    filepath = target_dir / filename

    fm = generate_frontmatter(
        date=date,
        source=source,
        tags=intent.tags,
        intent=intent.type,
        project=project,
        assigned=intent.person,
    )

    filepath.write_text(fm + "\n" + full_text + "\n")

    return filepath
