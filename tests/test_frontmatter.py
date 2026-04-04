"""Tests for YAML frontmatter generation."""

from datetime import datetime

from transcriber.frontmatter import generate_frontmatter, format_append_entry


def test_generate_frontmatter_basic():
    """Should generate valid YAML frontmatter."""
    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#todo", "#ai"],
    )
    assert fm.startswith("---\n")
    assert fm.endswith("---\n")
    assert "date: 2026-03-30T14:32:00" in fm
    assert "source: DJI_0042.WAV" in fm
    assert '"#todo"' in fm
    assert '"#ai"' in fm


def test_generate_frontmatter_with_intent():
    """Should include intent field when provided."""
    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#article_idea"],
        intent="article_idea",
    )
    assert "intent: article_idea" in fm


def test_generate_frontmatter_with_project():
    """Should include project field when provided."""
    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#summit_lab"],
        project="summit-lab",
    )
    assert "project: summit-lab" in fm


def test_generate_frontmatter_with_assigned():
    """Should include assigned field when provided."""
    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#todo", "#john"],
        assigned="John",
    )
    assert "assigned: John" in fm


def test_generate_frontmatter_deduplicates_tags():
    """Should deduplicate tags."""
    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#todo", "#ai", "#todo"],
    )
    assert fm.count('"#todo"') == 1


def test_format_append_entry_basic():
    """Should format a basic todo append entry."""
    entry = format_append_entry(
        content="Watch the Nvidia keynote",
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#nvidia", "#ai"],
    )
    assert "- [ ] Watch the Nvidia keynote" in entry
    assert "2026-03-30 14:32" in entry
    assert "DJI_0042.WAV" in entry
    assert "#nvidia" in entry


def test_format_append_entry_with_assigned():
    """Should include assigned line when person provided."""
    entry = format_append_entry(
        content="Speak to John about attending KubeCon",
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#john", "#kubecon"],
        assigned="John",
    )
    assert "Assigned: John" in entry


def test_format_append_entry_with_source_transcript():
    """Should include extracted-from line for embedded intents."""
    entry = format_append_entry(
        content="Check CI pipeline status",
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#todo"],
        source_transcript="transcript-DJI_0042.md",
    )
    assert "*Extracted from: transcript-DJI_0042.md*" in entry
