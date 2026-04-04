"""Tests for output dispatch (append and file modes)."""

from datetime import datetime
from pathlib import Path

from transcriber.dispatch import append_to_file, write_intent_file
from transcriber.router import ExtractedIntent


def test_append_to_file_creates_new(tmp_path: Path):
    """Should create target file if it doesn't exist."""
    target = tmp_path / "todos.md"
    intent = ExtractedIntent(
        type="todo", content="Buy milk", trigger="todo",
        position="start", tags=["#todo"],
    )
    append_to_file(
        target=target, intent=intent,
        date=datetime(2026, 3, 30, 14, 32), source="DJI_0042.WAV",
    )
    assert target.exists()
    content = target.read_text()
    assert "- [ ] Buy milk" in content
    assert "DJI_0042.WAV" in content


def test_append_to_file_appends_existing(tmp_path: Path):
    """Should append to existing file without overwriting."""
    target = tmp_path / "todos.md"
    target.write_text("- [ ] Existing todo\n")

    intent = ExtractedIntent(
        type="todo", content="New todo", trigger="todo",
        position="start", tags=["#todo"],
    )
    append_to_file(
        target=target, intent=intent,
        date=datetime(2026, 3, 30, 14, 32), source="DJI_0042.WAV",
    )
    content = target.read_text()
    assert "Existing todo" in content
    assert "New todo" in content


def test_append_to_file_with_person(tmp_path: Path):
    """Should include assigned field for person intents."""
    target = tmp_path / "todos.md"
    intent = ExtractedIntent(
        type="todo", content="attending KubeCon", trigger="speak to {person} about",
        person="John", position="start", tags=["#todo", "#john"],
    )
    append_to_file(
        target=target, intent=intent,
        date=datetime(2026, 3, 30, 14, 32), source="DJI_0042.WAV",
    )
    content = target.read_text()
    assert "Assigned: John" in content


def test_append_to_file_embedded_shows_source(tmp_path: Path):
    """Should show source transcript for embedded intents."""
    target = tmp_path / "todos.md"
    intent = ExtractedIntent(
        type="todo", content="Check CI", trigger="todo",
        position="embedded", tags=["#todo"],
    )
    append_to_file(
        target=target, intent=intent,
        date=datetime(2026, 3, 30, 14, 32), source="DJI_0042.WAV",
        source_transcript="transcript-DJI_0042.md",
    )
    content = target.read_text()
    assert "*Extracted from: transcript-DJI_0042.md*" in content


def test_write_intent_file(tmp_path: Path):
    """Should create individual file with frontmatter and content."""
    target_dir = tmp_path / "article-ideas"
    intent = ExtractedIntent(
        type="article_idea", content="Why voice capture changes everything",
        trigger="article idea", position="start", tags=["#article_idea"],
    )
    result_path = write_intent_file(
        target_dir=target_dir, intent=intent,
        date=datetime(2026, 3, 30, 14, 32), source="DJI_0042.WAV",
        full_text="Article idea why voice capture changes everything. It lets you think out loud.",
    )
    assert result_path.exists()
    assert result_path.parent == target_dir
    content = result_path.read_text()
    assert "---" in content
    assert "#article_idea" in content
    assert "voice capture" in content.lower()


def test_write_intent_file_uses_date_prefix(tmp_path: Path):
    """Output filename should start with date."""
    target_dir = tmp_path / "blogs"
    intent = ExtractedIntent(
        type="blog", content="Agentic DevOps deep dive",
        trigger="blog post", position="start", tags=["#blog"],
    )
    result_path = write_intent_file(
        target_dir=target_dir, intent=intent,
        date=datetime(2026, 3, 30, 14, 32), source="DJI_0042.WAV",
        full_text="Blog post agentic devops deep dive. Here are my thoughts.",
    )
    assert result_path.name.startswith("2026-03-30")
    assert result_path.suffix == ".md"
