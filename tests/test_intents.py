"""Tests for intent configuration loading."""

from pathlib import Path

import pytest

from transcriber.intents import IntentConfig, load_intents


def test_load_intents_from_yaml(tmp_path: Path):
    """Should load intent definitions from YAML file."""
    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: todo
    triggers:
      - "todo"
      - "to do"
    output: append
    target: "todos.md"
""")
    intents = load_intents(intents_file)
    assert len(intents) == 1
    assert intents[0].type == "todo"
    assert intents[0].triggers == ["todo", "to do"]
    assert intents[0].output == "append"
    assert intents[0].target == "todos.md"


def test_load_intents_with_person_extraction(tmp_path: Path):
    """Should load intents with {person} extraction config."""
    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: todo
    triggers:
      - "speak to {person} about"
    output: append
    target: "todos.md"
    extract:
      person: frontmatter
""")
    intents = load_intents(intents_file)
    assert intents[0].extract == {"person": "frontmatter"}


def test_load_intents_file_output_mode(tmp_path: Path):
    """Should support file output mode with directory target."""
    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: article_idea
    triggers:
      - "article idea"
    output: file
    target: "article-ideas/"
""")
    intents = load_intents(intents_file)
    assert intents[0].output == "file"
    assert intents[0].target == "article-ideas/"


def test_load_intents_missing_file():
    """Should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_intents(Path("/nonexistent/intents.yaml"))


def test_intent_config_defaults():
    """IntentConfig should have sensible defaults for optional fields."""
    intent = IntentConfig(type="todo", triggers=["todo"], output="append", target="todos.md")
    assert intent.extract == {}


def test_load_builtin_intents():
    """Should load built-in intents when no custom file is provided."""
    from transcriber.intents import load_builtin_intents

    intents = load_builtin_intents()
    types = [i.type for i in intents]
    assert "todo" in types
    assert "article_idea" in types
    assert "note" in types
    assert "blog" in types
