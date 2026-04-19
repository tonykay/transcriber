"""Tests for term correction dictionary."""

from pathlib import Path

import pytest

from transcriber.dictionary import (
    Dictionary,
    find_dictionaries,
    load_builtin_dictionaries,
    load_dictionary,
    load_dictionaries,
)


def test_dictionary_apply_simple():
    """Dictionary should replace wrong terms with correct ones."""
    d = Dictionary(corrections=[{"wrong": "Long Chain", "right": "LangChain"}])
    result = d.apply("I used Long Chain for this project.")
    assert result == "I used LangChain for this project."


def test_dictionary_apply_case_insensitive():
    """Corrections should be case-insensitive."""
    d = Dictionary(corrections=[{"wrong": "open shift", "right": "OpenShift"}])
    result = d.apply("We deployed on OPEN SHIFT today.")
    assert "OpenShift" in result


def test_dictionary_apply_multiple():
    """Multiple corrections should all be applied."""
    d = Dictionary(corrections=[
        {"wrong": "Long Chain", "right": "LangChain"},
        {"wrong": "Open Shift", "right": "OpenShift"},
    ])
    result = d.apply("Using Long Chain with Open Shift.")
    assert result == "Using LangChain with OpenShift."


def test_dictionary_apply_no_match():
    """Text without matching terms should be returned unchanged."""
    d = Dictionary(corrections=[{"wrong": "xyz123", "right": "ABC"}])
    text = "Nothing to correct here."
    assert d.apply(text) == text


def test_dictionary_empty():
    """Empty dictionary should return text unchanged."""
    d = Dictionary()
    text = "No corrections."
    assert d.apply(text) == text


def test_load_dictionary(tmp_path: Path):
    """Should load corrections from YAML file."""
    yaml_file = tmp_path / "terms.yaml"
    yaml_file.write_text("""
corrections:
  - wrong: "pie torch"
    right: "PyTorch"
  - wrong: "tensor flow"
    right: "TensorFlow"
""")
    d = load_dictionary(yaml_file)
    assert len(d.corrections) == 2
    assert d.apply("I used pie torch.") == "I used PyTorch."


def test_load_dictionary_missing(tmp_path: Path):
    """Should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_dictionary(tmp_path / "nonexistent.yaml")


def test_load_dictionaries_merges(tmp_path: Path):
    """Should merge multiple dictionary files."""
    f1 = tmp_path / "a.yaml"
    f1.write_text('corrections:\n  - wrong: "aaa"\n    right: "AAA"\n')
    f2 = tmp_path / "b.yaml"
    f2.write_text('corrections:\n  - wrong: "bbb"\n    right: "BBB"\n')

    d = load_dictionaries([f1, f2])
    assert len(d.corrections) == 2


def test_load_dictionaries_skips_missing(tmp_path: Path):
    """Should skip non-existent files without error."""
    f1 = tmp_path / "exists.yaml"
    f1.write_text('corrections:\n  - wrong: "x"\n    right: "X"\n')

    d = load_dictionaries([f1, tmp_path / "missing.yaml"])
    assert len(d.corrections) == 1


def test_find_dictionaries(tmp_path: Path):
    """Should find YAML files in search directories."""
    (tmp_path / "terms.yaml").write_text("corrections: []")
    (tmp_path / "extra.yml").write_text("corrections: []")
    (tmp_path / "ignore.txt").write_text("not a dict")

    found = find_dictionaries([tmp_path])
    names = [f.name for f in found]
    assert "terms.yaml" in names
    assert "extra.yml" in names
    assert "ignore.txt" not in names


def test_load_builtin_dictionaries():
    """Should load the built-in Red Hat ecosystem dictionary."""
    d = load_builtin_dictionaries()
    assert len(d.corrections) > 0
    assert d.apply("I used open claw for the demo.") == "I used OpenClaw for the demo."


def test_load_builtin_dictionaries_includes_key_terms():
    """Built-in dictionary should include essential domain terms."""
    d = load_builtin_dictionaries()
    assert "OpenShift" in d.apply("We deployed on open shift.")
    assert "LangChain" in d.apply("I used lang chain.")
    assert "kubectl" in d.apply("Run cube control get pods.")
