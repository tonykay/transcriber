"""Intent configuration loading and parsing."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


BUILTIN_INTENTS_FILE = Path(__file__).parent / "builtin_intents.yaml"


@dataclass
class IntentConfig:
    """A single intent definition from intents.yaml."""

    type: str
    triggers: list[str]
    output: str  # "append" or "file"
    target: str  # filename for append, directory for file
    extract: dict[str, str] = field(default_factory=dict)


def load_intents(path: Path) -> list[IntentConfig]:
    """Load intent definitions from a YAML file.

    Args:
        path: Path to intents YAML file.

    Returns:
        List of IntentConfig instances.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Intents file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    intents = []
    for item in data.get("intents", []):
        intents.append(
            IntentConfig(
                type=item["type"],
                triggers=item["triggers"],
                output=item["output"],
                target=item["target"],
                extract=item.get("extract", {}),
            )
        )
    return intents


def load_builtin_intents() -> list[IntentConfig]:
    """Load built-in intent definitions shipped with the package.

    Returns:
        List of IntentConfig for default intents.
    """
    return load_intents(BUILTIN_INTENTS_FILE)
