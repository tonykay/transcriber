"""Auto-classification and sorting of transcripts into project directories."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ClassifyRule:
    """A single classification rule."""

    project: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class ClassifyResult:
    """Result of classifying a transcript."""

    file: Path
    project: str
    destination: Path
    matched_keyword: str | None = None


def load_rules(path: Path) -> list[ClassifyRule]:
    """Load classification rules from a YAML file.

    YAML format:
        projects:
          - name: "langchain-project"
            keywords: ["langchain", "lang chain", "vector store"]
          - name: "openshift-work"
            keywords: ["openshift", "kubernetes", "k8s"]

    Args:
        path: Path to YAML rules file.

    Returns:
        List of ClassifyRule instances.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    rules = []
    for project in data.get("projects", []):
        rules.append(
            ClassifyRule(
                project=project["name"],
                keywords=project.get("keywords", []),
            )
        )
    return rules


def classify_text(text: str, rules: list[ClassifyRule]) -> tuple[str, str | None]:
    """Classify text content against rules.

    Checks text against each rule's keywords (case-insensitive).
    Returns the first matching project.

    Args:
        text: Transcript text to classify.
        rules: Classification rules to check against.

    Returns:
        Tuple of (project_name, matched_keyword). Project defaults to "misc"
        if no rules match.
    """
    text_lower = text.lower()

    for rule in rules:
        for keyword in rule.keywords:
            if keyword.lower() in text_lower:
                return rule.project, keyword

    return "misc", None


def sort_transcript(
    file: Path,
    projects_dir: Path,
    rules: list[ClassifyRule],
    move: bool = True,
) -> ClassifyResult:
    """Classify and sort a transcript file into a project directory.

    Args:
        file: Path to transcript file.
        projects_dir: Base directory containing project subdirectories.
        rules: Classification rules.
        move: If True, move the file. If False, copy.

    Returns:
        ClassifyResult with classification details.
    """
    text = file.read_text()
    project, keyword = classify_text(text, rules)

    dest_dir = projects_dir / project
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / file.name

    if move:
        shutil.move(str(file), str(dest_file))
    else:
        shutil.copy2(str(file), str(dest_file))

    return ClassifyResult(
        file=file,
        project=project,
        destination=dest_file,
        matched_keyword=keyword,
    )
