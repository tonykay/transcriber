"""Term correction using YAML-based dictionaries."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Dictionary:
    """A collection of term corrections loaded from YAML files.

    YAML format:
        corrections:
          - wrong: "Long Chain"
            right: "LangChain"
          - wrong: "para keet"
            right: "Parakeet"
    """

    corrections: list[dict[str, str]] = field(default_factory=list)

    def apply(self, text: str) -> str:
        """Apply all corrections to text using case-insensitive replacement.

        Args:
            text: Input text to correct.

        Returns:
            Text with corrections applied.
        """
        for entry in self.corrections:
            wrong = entry["wrong"]
            right = entry["right"]
            # Case-insensitive whole-word replacement
            pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            text = pattern.sub(right, text)
        return text


def load_dictionary(path: Path) -> Dictionary:
    """Load a dictionary from a YAML file.

    Args:
        path: Path to YAML dictionary file.

    Returns:
        Dictionary with loaded corrections.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    corrections = data.get("corrections", [])
    return Dictionary(corrections=corrections)


def load_dictionaries(paths: list[Path]) -> Dictionary:
    """Load and merge multiple dictionary files.

    Args:
        paths: List of paths to YAML dictionary files.

    Returns:
        Single Dictionary with all corrections merged.
    """
    all_corrections: list[dict[str, str]] = []
    for path in paths:
        if path.exists():
            d = load_dictionary(path)
            all_corrections.extend(d.corrections)
    return Dictionary(corrections=all_corrections)


def find_dictionaries(search_dirs: list[Path]) -> list[Path]:
    """Find dictionary YAML files in search directories.

    Args:
        search_dirs: Directories to search for *.yaml files.

    Returns:
        List of found dictionary file paths.
    """
    found: list[Path] = []
    for d in search_dirs:
        if d.is_dir():
            found.extend(sorted(d.glob("*.yaml")))
            found.extend(sorted(d.glob("*.yml")))
    return found
