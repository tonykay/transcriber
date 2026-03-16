"""Tests for auto-classification of transcripts."""

from pathlib import Path

from transcriber.classify import ClassifyRule, classify_text, load_rules, sort_transcript


def test_classify_text_matches_keyword():
    """Should match first matching keyword."""
    rules = [
        ClassifyRule(project="langchain", keywords=["langchain", "vector store"]),
        ClassifyRule(project="openshift", keywords=["openshift", "k8s"]),
    ]
    project, keyword = classify_text("Today I worked on LangChain agents.", rules)
    assert project == "langchain"
    assert keyword == "langchain"


def test_classify_text_case_insensitive():
    """Keyword matching should be case-insensitive."""
    rules = [ClassifyRule(project="k8s", keywords=["kubernetes"])]
    project, keyword = classify_text("Deployed on KUBERNETES cluster.", rules)
    assert project == "k8s"


def test_classify_text_no_match_returns_misc():
    """Should return 'misc' when no rules match."""
    rules = [ClassifyRule(project="langchain", keywords=["langchain"])]
    project, keyword = classify_text("Just a random note about my day.", rules)
    assert project == "misc"
    assert keyword is None


def test_classify_text_first_match_wins():
    """Should return first matching project when text matches multiple."""
    rules = [
        ClassifyRule(project="first", keywords=["python"]),
        ClassifyRule(project="second", keywords=["python"]),
    ]
    project, _ = classify_text("Learning python today.", rules)
    assert project == "first"


def test_classify_text_empty_rules():
    """Empty rules should classify everything as misc."""
    project, keyword = classify_text("Anything here.", [])
    assert project == "misc"
    assert keyword is None


def test_load_rules(tmp_path: Path):
    """Should load rules from YAML file."""
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("""
projects:
  - name: "ai-project"
    keywords: ["machine learning", "neural network"]
  - name: "devops"
    keywords: ["ci/cd", "pipeline"]
""")
    rules = load_rules(rules_file)
    assert len(rules) == 2
    assert rules[0].project == "ai-project"
    assert "machine learning" in rules[0].keywords


def test_sort_transcript_moves_to_project(tmp_path: Path):
    """Should move transcript to matching project directory."""
    # Create a transcript file
    transcript = tmp_path / "transcript.md"
    transcript.write_text("Working on LangChain agents today.")

    projects_dir = tmp_path / "projects"

    rules = [ClassifyRule(project="langchain", keywords=["langchain"])]

    result = sort_transcript(transcript, projects_dir, rules)

    assert result.project == "langchain"
    assert result.destination == projects_dir / "langchain" / "transcript.md"
    assert result.destination.exists()
    assert not transcript.exists()  # original moved


def test_sort_transcript_misc_fallback(tmp_path: Path):
    """Should sort to misc/ when no rules match."""
    transcript = tmp_path / "random.md"
    transcript.write_text("Just a random thought.")

    projects_dir = tmp_path / "projects"
    rules = [ClassifyRule(project="langchain", keywords=["langchain"])]

    result = sort_transcript(transcript, projects_dir, rules)

    assert result.project == "misc"
    assert result.destination == projects_dir / "misc" / "random.md"
    assert result.destination.exists()


def test_sort_transcript_copy_mode(tmp_path: Path):
    """Should copy instead of move when move=False."""
    transcript = tmp_path / "keep-original.md"
    transcript.write_text("OpenShift deployment notes.")

    projects_dir = tmp_path / "projects"
    rules = [ClassifyRule(project="openshift", keywords=["openshift"])]

    result = sort_transcript(transcript, projects_dir, rules, move=False)

    assert result.destination.exists()
    assert transcript.exists()  # original preserved
