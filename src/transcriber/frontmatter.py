"""YAML frontmatter generation for Obsidian-compatible outputs."""

from datetime import datetime


def generate_frontmatter(
    date: datetime,
    source: str,
    tags: list[str],
    intent: str | None = None,
    project: str | None = None,
    assigned: str | None = None,
) -> str:
    """Generate YAML frontmatter block.

    Args:
        date: Timestamp of the recording.
        source: Source audio filename.
        tags: List of tags, each prefixed with #.
        intent: Detected intent type.
        project: Classified project name.
        assigned: Assigned person name.

    Returns:
        YAML frontmatter string including --- delimiters.
    """
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    tag_str = ", ".join(f'"{t}"' for t in unique_tags)

    lines = [
        "---",
        f"date: {date.isoformat()}",
        f"source: {source}",
        f"tags: [{tag_str}]",
    ]

    if intent:
        lines.append(f"intent: {intent}")
    if project:
        lines.append(f"project: {project}")
    if assigned:
        lines.append(f"assigned: {assigned}")

    lines.append("---")

    return "\n".join(lines) + "\n"


def format_append_entry(
    content: str,
    date: datetime,
    source: str,
    tags: list[str],
    assigned: str | None = None,
    source_transcript: str | None = None,
) -> str:
    """Format an entry for appending to a capture file (todos.md, notes.md).

    Args:
        content: The extracted content text.
        date: Timestamp of the recording.
        source: Source audio filename.
        tags: List of tags, each prefixed with #.
        assigned: Assigned person name.
        source_transcript: Filename of full transcript (for embedded intents).

    Returns:
        Formatted markdown entry string.
    """
    tag_str = " ".join(tags)
    date_str = date.strftime("%Y-%m-%d %H:%M")

    lines = [
        f"- [ ] {content}",
        f"  `{date_str} | {source} | {tag_str}`",
    ]

    if assigned:
        lines.append(f"  Assigned: {assigned}")

    if source_transcript:
        lines.append(f"  *Extracted from: {source_transcript}*")

    return "\n".join(lines) + "\n"
