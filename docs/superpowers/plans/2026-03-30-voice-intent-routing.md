# Voice Intent Routing & Smart Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a two-pass hybrid router that detects voice triggers in transcripts, extracts actionable items, generates Obsidian-compatible frontmatter, and dispatches outputs to the right files/directories.

**Architecture:** A new `router.py` module sits between LLM formatting and file output in the pipeline. Pass 1 uses regex to match explicit triggers from a YAML config. Pass 2 (LLM fallback) fires only when no triggers are found. A `frontmatter.py` module generates YAML frontmatter with tags. A `dispatch.py` module handles appending to files vs creating individual files.

**Tech Stack:** Python 3.13, Pydantic V2, PyYAML, regex, existing Ollama provider for LLM fallback.

**Spec:** `docs/superpowers/specs/2026-03-30-voice-intent-routing-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/transcriber/config.py` | **Modify** — move paths under `.processing/`, add `RouterConfig` |
| `src/transcriber/intents.py` | **Create** — load and parse `intents.yaml` trigger definitions |
| `src/transcriber/router.py` | **Create** — two-pass intent detection (regex + LLM fallback) |
| `src/transcriber/frontmatter.py` | **Create** — YAML frontmatter generation with tags |
| `src/transcriber/dispatch.py` | **Create** — output dispatch: append-to-file and file-per-recording |
| `src/transcriber/classify.py` | **Modify** — return tags alongside project name |
| `src/transcriber/pipeline.py` | **Modify** — integrate router + dispatch after LLM step |
| `src/transcriber/cli.py` | **Modify** — add `--no-llm-fallback` flag |
| `src/transcriber/builtin_intents.yaml` | **Create** — default intent trigger definitions shipped with package |
| `tests/test_intents.py` | **Create** — intent loading tests |
| `tests/test_router.py` | **Create** — router unit tests |
| `tests/test_frontmatter.py` | **Create** — frontmatter generation tests |
| `tests/test_dispatch.py` | **Create** — dispatch output tests |

---

### Task 1: Update PathsConfig to use `.processing/` subdirectory

**Files:**
- Modify: `src/transcriber/config.py:9-34`
- Modify: `tests/test_config.py`
- Modify: `tests/test_e2e.py`

- [ ] **Step 1: Write failing test for new path layout**

In `tests/test_config.py`, add:

```python
def test_paths_use_processing_subdirectory():
    """Intermediate paths should be under .processing/ subdirectory."""
    config = PathsConfig(base="/tmp/transcripts")
    assert ".processing" in config.audio_unprocessed
    assert ".processing" in config.audio_processed
    assert ".processing" in config.text_unprocessed
    assert ".processing" in config.text_processed
    # Final output paths should NOT be under .processing
    assert ".processing" not in config.transcripts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_paths_use_processing_subdirectory -v`
Expected: FAIL — current paths don't include `.processing`

- [ ] **Step 3: Update PathsConfig to use `.processing/`**

In `src/transcriber/config.py`, change the four intermediate path properties:

```python
class PathsConfig(BaseModel):
    """Directory paths configuration."""

    base: str = "~/Resources/Transcripts"
    dji_source: str = "/Volumes/DJI_MIC2"

    @property
    def audio_unprocessed(self) -> str:
        return str(Path(self.base).expanduser() / ".processing" / "audio-unprocessed")

    @property
    def audio_processed(self) -> str:
        return str(Path(self.base).expanduser() / ".processing" / "audio-processed")

    @property
    def text_unprocessed(self) -> str:
        return str(Path(self.base).expanduser() / ".processing" / "text-unprocessed")

    @property
    def text_processed(self) -> str:
        return str(Path(self.base).expanduser() / ".processing" / "text-processed")

    @property
    def transcripts(self) -> str:
        return str(Path(self.base).expanduser() / "transcripts")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_paths_use_processing_subdirectory -v`
Expected: PASS

- [ ] **Step 5: Fix existing tests that reference old paths**

In `tests/test_e2e.py`, update `test_pipeline_skip_import_with_existing_audio` to use `.processing/audio-unprocessed`:

```python
    # Pre-create audio in the unprocessed directory with correct ISO format
    audio_unprocessed_dir = temp_dirs["base"] / ".processing" / "audio-unprocessed"
    audio_unprocessed_dir.mkdir(parents=True)
```

In `test_pipeline_handles_missing_stt_provider`:

```python
    audio_unprocessed_dir = temp_dirs["base"] / ".processing" / "audio-unprocessed"
    audio_unprocessed_dir.mkdir(parents=True)
```

In `test_pipeline_creates_output_directories`, update the assertions:

```python
    # Verify key directories were created
    assert (temp_dirs["base"] / ".processing" / "audio-unprocessed").exists()
    assert (temp_dirs["base"] / ".processing" / "audio-processed").exists()
    assert (temp_dirs["base"] / ".processing" / "text-unprocessed").exists() or (
        temp_dirs["base"] / ".processing" / "text-processed"
    ).exists()
```

- [ ] **Step 6: Run full test suite to verify nothing broke**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add src/transcriber/config.py tests/test_config.py tests/test_e2e.py
git commit -m "refactor: move intermediate paths under .processing/ subdirectory"
```

---

### Task 2: Add RouterConfig to config

**Files:**
- Modify: `src/transcriber/config.py:62-78`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write failing test**

In `tests/test_config.py`, add:

```python
def test_router_config_defaults():
    """RouterConfig should have sensible defaults."""
    config = TranscriberConfig()
    assert config.router.llm_fallback is True
    assert config.router.intents_file is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_router_config_defaults -v`
Expected: FAIL — `TranscriberConfig` has no `router` attribute

- [ ] **Step 3: Add RouterConfig**

In `src/transcriber/config.py`, add the new model and wire it in:

```python
class RouterConfig(BaseModel):
    """Intent routing configuration."""

    intents_file: str | None = None
    llm_fallback: bool = True
```

Add to `TranscriberConfig`:

```python
class TranscriberConfig(BaseModel):
    """Main configuration for transcriber."""

    paths: PathsConfig = PathsConfig()
    stt: STTConfig = STTConfig()
    llm: LLMConfig = LLMConfig()
    output: OutputConfig = OutputConfig()
    dictionaries: DictionaryConfig = DictionaryConfig()
    classify: ClassifyConfig = ClassifyConfig()
    router: RouterConfig = RouterConfig()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_router_config_defaults -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/config.py tests/test_config.py
git commit -m "feat: add RouterConfig for intent routing settings"
```

---

### Task 3: Create intent config loading

**Files:**
- Create: `src/transcriber/intents.py`
- Create: `tests/test_intents.py`

- [ ] **Step 1: Write failing tests for intent loading**

Create `tests/test_intents.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_intents.py -v`
Expected: FAIL — module `transcriber.intents` does not exist

- [ ] **Step 3: Implement intents module**

Create `src/transcriber/intents.py`:

```python
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
```

- [ ] **Step 4: Create builtin_intents.yaml**

Create `src/transcriber/builtin_intents.yaml`:

```yaml
intents:
  - type: todo
    triggers:
      - "todo"
      - "to do"
      - "reminder"
    output: append
    target: "todos.md"

  - type: todo
    triggers:
      - "speak to {person} about"
      - "talk to {person} about"
      - "ask {person} about"
      - "tell {person} about"
    output: append
    target: "todos.md"
    extract:
      person: frontmatter

  - type: article_idea
    triggers:
      - "article idea"
      - "blog idea"
      - "writing idea"
    output: file
    target: "article-ideas/"

  - type: note
    triggers:
      - "note"
      - "quick note"
    output: append
    target: "notes.md"

  - type: blog
    triggers:
      - "blog post"
      - "blog draft"
    output: file
    target: "blogs/"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_intents.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add src/transcriber/intents.py src/transcriber/builtin_intents.yaml tests/test_intents.py
git commit -m "feat: add intent config loading from YAML"
```

---

### Task 4: Create router — Pass 1 simple trigger matching

**Files:**
- Create: `src/transcriber/router.py`
- Create: `tests/test_router.py`

- [ ] **Step 1: Write failing tests for simple trigger detection**

Create `tests/test_router.py`:

```python
"""Tests for intent router."""

from transcriber.intents import IntentConfig
from transcriber.router import ExtractedIntent, RoutingResult, route_text


def _todo_intent() -> IntentConfig:
    return IntentConfig(
        type="todo", triggers=["todo", "to do", "reminder"],
        output="append", target="todos.md",
    )


def _article_intent() -> IntentConfig:
    return IntentConfig(
        type="article_idea", triggers=["article idea", "blog idea"],
        output="file", target="article-ideas/",
    )


def _note_intent() -> IntentConfig:
    return IntentConfig(
        type="note", triggers=["note", "quick note"],
        output="append", target="notes.md",
    )


def test_route_text_detects_start_trigger():
    """Should detect trigger at start of text and set primary_intent."""
    result = route_text("Todo watch the Nvidia keynote", [_todo_intent()])
    assert result.primary_intent == "todo"
    assert len(result.extracted_intents) == 1
    assert result.extracted_intents[0].content == "watch the Nvidia keynote"
    assert result.extracted_intents[0].position == "start"


def test_route_text_case_insensitive():
    """Trigger matching should be case-insensitive."""
    result = route_text("TODO buy groceries", [_todo_intent()])
    assert result.primary_intent == "todo"


def test_route_text_strips_trigger_from_content():
    """Extracted content should not include the trigger phrase."""
    result = route_text("Reminder call the dentist", [_todo_intent()])
    assert result.extracted_intents[0].content == "call the dentist"
    assert result.extracted_intents[0].trigger == "reminder"


def test_route_text_no_match_returns_empty():
    """Should return no intents when no triggers match."""
    result = route_text("Just a regular transcript about my day.", [_todo_intent()])
    assert result.primary_intent is None
    assert result.extracted_intents == []


def test_route_text_multi_word_trigger():
    """Should match multi-word triggers like 'article idea'."""
    result = route_text("Article idea why voice capture changes everything", [_article_intent()])
    assert result.primary_intent == "article_idea"
    assert result.extracted_intents[0].content == "why voice capture changes everything"


def test_route_text_word_boundary():
    """Should not match 'to do' inside 'want to do something'."""
    result = route_text("I want to do something about this project.", [_todo_intent()])
    assert result.primary_intent is None
    assert result.extracted_intents == []


def test_route_text_trigger_with_punctuation():
    """Should match trigger followed by comma or colon."""
    result = route_text("Todo, watch the Nvidia keynote", [_todo_intent()])
    assert result.primary_intent == "todo"
    assert result.extracted_intents[0].content == "watch the Nvidia keynote"


def test_route_text_preserves_full_text():
    """RoutingResult should preserve the original full text."""
    text = "Todo buy milk"
    result = route_text(text, [_todo_intent()])
    assert result.full_text == text


def test_route_text_intent_tags():
    """Extracted intent should include type as a tag."""
    result = route_text("Todo buy milk", [_todo_intent()])
    assert "#todo" in result.extracted_intents[0].tags
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_router.py -v`
Expected: FAIL — module `transcriber.router` does not exist

- [ ] **Step 3: Implement router with Pass 1 simple trigger matching**

Create `src/transcriber/router.py`:

```python
"""Two-pass intent router for transcript classification."""

import re
from dataclasses import dataclass, field

from transcriber.intents import IntentConfig


@dataclass
class ExtractedIntent:
    """A single intent extracted from transcript text."""

    type: str
    content: str
    trigger: str
    person: str | None = None
    position: str = "start"  # "start" or "embedded"
    tags: list[str] = field(default_factory=list)


@dataclass
class RoutingResult:
    """Result of routing a transcript through intent detection."""

    primary_intent: str | None = None
    extracted_intents: list[ExtractedIntent] = field(default_factory=list)
    project: str | None = None
    tags: list[str] = field(default_factory=list)
    full_text: str = ""


def _has_person_placeholder(trigger: str) -> bool:
    """Check if a trigger contains a {person} placeholder."""
    return "{person}" in trigger


def _build_simple_pattern(trigger: str) -> re.Pattern[str]:
    """Build a regex pattern for a simple (non-person) trigger.

    Matches the trigger at a word boundary, optionally followed by
    punctuation (comma, colon, dash). Does NOT match the trigger
    when it appears as a substring of a larger phrase.
    """
    escaped = re.escape(trigger)
    # Match at start of text or after sentence boundary, with word boundaries
    # Followed by optional punctuation then content
    return re.compile(
        r"(?:^|(?<=\.\s)|(?<=\?\s)|(?<=!\s)|(?<=\n))"
        r"\s*"
        rf"(?P<trigger>{escaped})"
        r"[,:\-]?\s*"
        r"(?P<content>.*)",
        re.IGNORECASE | re.DOTALL,
    )


def _extract_sentence(text: str) -> str:
    """Extract content up to the next sentence boundary.

    Returns text up to the first ., !, or ? followed by a space or end,
    or the full text if no boundary is found.
    """
    match = re.search(r"[.!?](?:\s|$)", text)
    if match:
        return text[: match.start()].strip()
    return text.strip()


def route_text(text: str, intents: list[IntentConfig]) -> RoutingResult:
    """Route transcript text through Pass 1 (regex trigger matching).

    Scans text for trigger phrases defined in intents config.
    A trigger at the start sets primary_intent.
    Triggers found mid-text are extracted as embedded intents.

    Args:
        text: Transcript text to route.
        intents: Intent definitions to match against.

    Returns:
        RoutingResult with detected intents.
    """
    result = RoutingResult(full_text=text)
    text_stripped = text.strip()

    # Separate simple triggers from person-extraction triggers
    simple_intents = [i for i in intents if not any(_has_person_placeholder(t) for t in i.triggers)]
    # Person intents handled in Task 5

    # Check for start-of-text triggers
    for intent in simple_intents:
        for trigger in intent.triggers:
            pattern = _build_simple_pattern(trigger)
            match = pattern.match(text_stripped)
            if match:
                content = match.group("content").strip()
                extracted = ExtractedIntent(
                    type=intent.type,
                    content=content,
                    trigger=trigger.lower(),
                    position="start",
                    tags=[f"#{intent.type}"],
                )
                result.primary_intent = intent.type
                result.extracted_intents.append(extracted)
                return result

    # Embedded intent extraction handled in Task 6

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_router.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/router.py tests/test_router.py
git commit -m "feat: add router with Pass 1 simple trigger matching"
```

---

### Task 5: Add `{person}` extraction to router

**Files:**
- Modify: `src/transcriber/router.py`
- Modify: `tests/test_router.py`

- [ ] **Step 1: Write failing tests for person extraction**

Add to `tests/test_router.py`:

```python
def _person_intent() -> IntentConfig:
    return IntentConfig(
        type="todo",
        triggers=["speak to {person} about", "ask {person} about", "talk to {person} about", "tell {person} about"],
        output="append",
        target="todos.md",
        extract={"person": "frontmatter"},
    )


def test_route_text_person_extraction():
    """Should extract person name from 'speak to {person} about' trigger."""
    result = route_text("Speak to John about attending KubeCon", [_person_intent()])
    assert result.primary_intent == "todo"
    assert result.extracted_intents[0].person == "John"
    assert result.extracted_intents[0].content == "attending KubeCon"
    assert "#john" in result.extracted_intents[0].tags


def test_route_text_person_ask_variant():
    """Should handle 'ask {person} about' variant."""
    result = route_text("Ask Sarah about the deployment timeline", [_person_intent()])
    assert result.extracted_intents[0].person == "Sarah"
    assert result.extracted_intents[0].content == "the deployment timeline"


def test_route_text_person_case_insensitive():
    """Person extraction trigger should be case-insensitive."""
    result = route_text("TELL james about the new API", [_person_intent()])
    assert result.extracted_intents[0].person == "james"


def test_route_text_person_multi_word_name():
    """Should extract multi-word names before stop word."""
    result = route_text("Talk to Mary Jane about the project", [_person_intent()])
    assert result.extracted_intents[0].person == "Mary Jane"
    assert result.extracted_intents[0].content == "the project"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_router.py::test_route_text_person_extraction tests/test_router.py::test_route_text_person_ask_variant tests/test_router.py::test_route_text_person_case_insensitive tests/test_router.py::test_route_text_person_multi_word_name -v`
Expected: FAIL

- [ ] **Step 3: Implement person extraction**

In `src/transcriber/router.py`, add a function to build person-extraction patterns:

```python
_PERSON_STOP_WORDS = ("about", "regarding", "that")


def _build_person_pattern(trigger: str) -> re.Pattern[str]:
    """Build a regex pattern for a trigger with {person} placeholder.

    The {person} group captures one or more capitalized words (a name)
    up to a stop word like 'about', 'regarding', 'that'.
    """
    # Split trigger around {person}
    parts = trigger.split("{person}")
    before = re.escape(parts[0].strip())
    after = parts[1].strip() if len(parts) > 1 else ""
    after_escaped = re.escape(after).strip()

    # {person} captures words until the stop word
    return re.compile(
        r"(?:^|(?<=\.\s)|(?<=\?\s)|(?<=!\s)|(?<=\n))"
        r"\s*"
        rf"(?P<trigger_before>{before})\s+"
        r"(?P<person>[\w\s]+?)\s+"
        rf"{after_escaped}\s*"
        r"(?P<content>.*)",
        re.IGNORECASE | re.DOTALL,
    )
```

Update `route_text` to handle person intents — add this block before the "Check for start-of-text triggers" comment:

```python
    person_intents = [i for i in intents if any(_has_person_placeholder(t) for t in i.triggers)]

    # Check person-extraction triggers first (more specific)
    for intent in person_intents:
        for trigger in intent.triggers:
            if not _has_person_placeholder(trigger):
                continue
            pattern = _build_person_pattern(trigger)
            match = pattern.match(text_stripped)
            if match:
                person = match.group("person").strip()
                content = match.group("content").strip()
                tags = [f"#{intent.type}", f"#{person.lower().replace(' ', '_')}"]
                extracted = ExtractedIntent(
                    type=intent.type,
                    content=content,
                    trigger=trigger.lower(),
                    person=person,
                    position="start",
                    tags=tags,
                )
                result.primary_intent = intent.type
                result.extracted_intents.append(extracted)
                return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_router.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/transcriber/router.py tests/test_router.py
git commit -m "feat: add {person} extraction to router triggers"
```

---

### Task 6: Add embedded intent extraction to router

**Files:**
- Modify: `src/transcriber/router.py`
- Modify: `tests/test_router.py`

- [ ] **Step 1: Write failing tests for embedded extraction**

Add to `tests/test_router.py`:

```python
def test_route_text_embedded_intent():
    """Should extract embedded trigger from mid-text."""
    text = (
        "We should really show the GitOps workflow. "
        "Todo, ask James about the cluster quota limits. "
        "Anyway back to the demo flow."
    )
    result = route_text(text, [_todo_intent(), _person_intent()])
    assert result.primary_intent is None  # no start trigger
    assert len(result.extracted_intents) == 1
    intent = result.extracted_intents[0]
    assert intent.type == "todo"
    assert intent.position == "embedded"
    assert intent.person == "James"


def test_route_text_multiple_embedded():
    """Should extract multiple embedded intents."""
    text = (
        "Working on the summit lab. "
        "Todo buy new cables for the demo. "
        "Also, reminder to book flights."
    )
    result = route_text(text, [_todo_intent()])
    assert len(result.extracted_intents) == 2
    assert all(i.position == "embedded" for i in result.extracted_intents)


def test_route_text_start_plus_embedded():
    """Start trigger and embedded trigger should both fire."""
    text = (
        "Article idea why voice capture changes everything. "
        "Oh and todo, buy a new microphone."
    )
    result = route_text(text, [_todo_intent(), _article_intent()])
    assert result.primary_intent == "article_idea"
    assert len(result.extracted_intents) == 2
    types = [i.type for i in result.extracted_intents]
    assert "article_idea" in types
    assert "todo" in types


def test_route_text_embedded_sentence_boundary():
    """Embedded extraction should stop at sentence boundary."""
    text = (
        "General discussion here. "
        "Reminder check the CI pipeline status. "
        "Back to regular discussion."
    )
    result = route_text(text, [_todo_intent()])
    assert result.extracted_intents[0].content == "check the CI pipeline status"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_router.py::test_route_text_embedded_intent tests/test_router.py::test_route_text_multiple_embedded tests/test_router.py::test_route_text_start_plus_embedded tests/test_router.py::test_route_text_embedded_sentence_boundary -v`
Expected: FAIL

- [ ] **Step 3: Implement embedded intent extraction**

In `src/transcriber/router.py`, refactor `route_text` to scan the full text for embedded triggers after checking for a start trigger. Replace the embedded comment placeholder with:

```python
    # Scan for embedded triggers throughout the text
    embedded = _extract_embedded_intents(text_stripped, intents)
    result.extracted_intents.extend(embedded)

    return result
```

Add the implementation function:

```python
def _extract_embedded_intents(
    text: str, intents: list[IntentConfig]
) -> list[ExtractedIntent]:
    """Scan text for trigger phrases at sentence boundaries.

    Looks for triggers after sentence-ending punctuation (. ! ?)
    and extracts content up to the next sentence boundary.
    """
    extracted: list[ExtractedIntent] = []

    # Split text into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if not sentence_stripped:
            continue

        # Check person triggers first (more specific)
        person_intents = [i for i in intents if any(_has_person_placeholder(t) for t in i.triggers)]
        matched = False

        for intent in person_intents:
            if matched:
                break
            for trigger in intent.triggers:
                if not _has_person_placeholder(trigger):
                    continue
                pattern = _build_person_pattern(trigger)
                match = pattern.match(sentence_stripped)
                if match:
                    person = match.group("person").strip()
                    content = _extract_sentence(match.group("content").strip())
                    tags = [f"#{intent.type}", f"#{person.lower().replace(' ', '_')}"]
                    extracted.append(ExtractedIntent(
                        type=intent.type,
                        content=content,
                        trigger=trigger.lower(),
                        person=person,
                        position="embedded",
                        tags=tags,
                    ))
                    matched = True
                    break

        if matched:
            continue

        # Check simple triggers
        simple_intents = [i for i in intents if not any(_has_person_placeholder(t) for t in i.triggers)]
        for intent in simple_intents:
            if matched:
                break
            for trigger in intent.triggers:
                pattern = _build_simple_pattern(trigger)
                match = pattern.match(sentence_stripped)
                if match:
                    content = _extract_sentence(match.group("content").strip())
                    extracted.append(ExtractedIntent(
                        type=intent.type,
                        content=content,
                        trigger=trigger.lower(),
                        position="embedded",
                        tags=[f"#{intent.type}"],
                    ))
                    matched = True
                    break

    return extracted
```

Update `route_text` so that when a start trigger is found, the remaining text is still scanned for embedded intents. After the start-trigger return statements, remove the early `return result` and instead continue to scan:

```python
    # After finding a start trigger, scan remaining text for embedded intents
    if result.primary_intent:
        # Get text after the first sentence for embedded scanning
        remaining_sentences = re.split(r"(?<=[.!?])\s+", text_stripped)
        if len(remaining_sentences) > 1:
            remaining_text = " ".join(remaining_sentences[1:])
            embedded = _extract_embedded_intents(remaining_text, intents)
            result.extracted_intents.extend(embedded)
        return result

    # No start trigger — scan entire text for embedded intents
    embedded = _extract_embedded_intents(text_stripped, intents)
    result.extracted_intents.extend(embedded)

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_router.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/router.py tests/test_router.py
git commit -m "feat: add embedded intent extraction to router"
```

---

### Task 7: Create frontmatter module

**Files:**
- Create: `src/transcriber/frontmatter.py`
- Create: `tests/test_frontmatter.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_frontmatter.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_frontmatter.py -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Implement frontmatter module**

Create `src/transcriber/frontmatter.py`:

```python
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
    # Deduplicate tags preserving order
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_frontmatter.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/transcriber/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: add frontmatter module for Obsidian-compatible output"
```

---

### Task 8: Create dispatch module

**Files:**
- Create: `src/transcriber/dispatch.py`
- Create: `tests/test_dispatch.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_dispatch.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dispatch.py -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Implement dispatch module**

Create `src/transcriber/dispatch.py`:

```python
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

    # Generate filename from date + content slug
    slug = _slugify(intent.content[:60])
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    filepath = target_dir / filename

    # Generate frontmatter
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_dispatch.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/dispatch.py tests/test_dispatch.py
git commit -m "feat: add dispatch module for append and file output"
```

---

### Task 9: Update classify.py to return tags

**Files:**
- Modify: `src/transcriber/classify.py:58-79`
- Modify: `tests/test_classify.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_classify.py`:

```python
def test_classify_text_returns_tags():
    """Should return tags from matched keywords."""
    rules = [
        ClassifyRule(project="summit-lab", keywords=["summit", "agentic", "devops"]),
    ]
    project, keyword, tags = classify_text(
        "In our Summit Agentic DevOps lab we should add more demos.", rules
    )
    assert project == "summit-lab"
    assert "#summit_lab" in tags
    assert "#summit" in tags


def test_classify_text_no_match_returns_empty_tags():
    """Should return empty tags when nothing matches."""
    rules = [ClassifyRule(project="langchain", keywords=["langchain"])]
    project, keyword, tags = classify_text("Random note about my day.", rules)
    assert project == "misc"
    assert tags == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_classify.py::test_classify_text_returns_tags tests/test_classify.py::test_classify_text_no_match_returns_empty_tags -v`
Expected: FAIL — `classify_text` returns 2 values, not 3

- [ ] **Step 3: Update classify_text to return tags**

In `src/transcriber/classify.py`, update `classify_text`:

```python
def classify_text(text: str, rules: list[ClassifyRule]) -> tuple[str, str | None, list[str]]:
    """Classify text content against rules.

    Checks text against each rule's keywords (case-insensitive).
    Returns the first matching project with tags.

    Args:
        text: Transcript text to classify.
        rules: Classification rules to check against.

    Returns:
        Tuple of (project_name, matched_keyword, tags).
        Project defaults to "misc" if no rules match.
        Tags include the project name and all matched keywords, prefixed with #.
    """
    text_lower = text.lower()

    for rule in rules:
        for keyword in rule.keywords:
            if keyword.lower() in text_lower:
                # Collect all matching keywords as tags
                tags = [f"#{rule.project.replace('-', '_')}"]
                for kw in rule.keywords:
                    if kw.lower() in text_lower:
                        tag = f"#{kw.lower().replace(' ', '_').replace('-', '_')}"
                        if tag not in tags:
                            tags.append(tag)
                return rule.project, keyword, tags

    return "misc", None, []
```

- [ ] **Step 4: Update existing callers and tests**

Update `tests/test_classify.py` — all existing tests that unpack 2 values need to unpack 3:

```python
def test_classify_text_matches_keyword():
    """Should match first matching keyword."""
    rules = [
        ClassifyRule(project="langchain", keywords=["langchain", "vector store"]),
        ClassifyRule(project="openshift", keywords=["openshift", "k8s"]),
    ]
    project, keyword, _tags = classify_text("Today I worked on LangChain agents.", rules)
    assert project == "langchain"
    assert keyword == "langchain"


def test_classify_text_case_insensitive():
    """Keyword matching should be case-insensitive."""
    rules = [ClassifyRule(project="k8s", keywords=["kubernetes"])]
    project, keyword, _tags = classify_text("Deployed on KUBERNETES cluster.", rules)
    assert project == "k8s"


def test_classify_text_no_match_returns_misc():
    """Should return 'misc' when no rules match."""
    rules = [ClassifyRule(project="langchain", keywords=["langchain"])]
    project, keyword, _tags = classify_text("Just a random note about my day.", rules)
    assert project == "misc"
    assert keyword is None


def test_classify_text_first_match_wins():
    """Should return first matching project when text matches multiple."""
    rules = [
        ClassifyRule(project="first", keywords=["python"]),
        ClassifyRule(project="second", keywords=["python"]),
    ]
    project, _, _tags = classify_text("Learning python today.", rules)
    assert project == "first"


def test_classify_text_empty_rules():
    """Empty rules should classify everything as misc."""
    project, keyword, tags = classify_text("Anything here.", [])
    assert project == "misc"
    assert keyword is None
    assert tags == []
```

Update `src/transcriber/classify.py` in `sort_transcript`:

```python
    text = file.read_text()
    project, keyword, _tags = classify_text(text, rules)
```

Update `src/transcriber/pipeline.py` in `_classify_transcripts` — no changes needed there since `sort_transcript` handles it internally.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_classify.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add src/transcriber/classify.py tests/test_classify.py
git commit -m "feat: return tags from classify_text for frontmatter integration"
```

---

### Task 10: Add LLM fallback (Pass 2) to router

**Files:**
- Modify: `src/transcriber/router.py`
- Modify: `tests/test_router.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_router.py`:

```python
import json
from unittest.mock import MagicMock, patch


def test_route_text_with_llm_fallback():
    """Should use LLM fallback when no regex triggers match."""
    llm_response = json.dumps({
        "intents": [{"type": "todo", "content": "review the PR", "position": "embedded"}],
        "suggested_tags": ["#code_review"],
    })

    mock_provider = MagicMock()
    mock_provider.is_available.return_value = True
    mock_result = MagicMock()
    mock_result.stdout = llm_response
    mock_provider.classify.return_value = mock_result

    result = route_text_with_fallback(
        text="I should probably review that pull request soon.",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert len(result.extracted_intents) == 1
    assert result.extracted_intents[0].type == "todo"
    assert result.extracted_intents[0].content == "review the PR"


def test_route_text_with_llm_fallback_no_intent():
    """LLM fallback returning 'none' should produce empty result."""
    llm_response = json.dumps({
        "intents": [{"type": "none", "content": "", "position": "start"}],
        "suggested_tags": ["#general"],
    })

    mock_provider = MagicMock()
    mock_provider.is_available.return_value = True
    mock_result = MagicMock()
    mock_result.stdout = llm_response
    mock_provider.classify.return_value = mock_result

    result = route_text_with_fallback(
        text="Just chatting about the weather today.",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert result.primary_intent is None
    assert result.extracted_intents == []
    assert "#general" in result.tags


def test_route_text_with_llm_fallback_skipped_when_regex_matches():
    """LLM fallback should NOT fire when regex already matched."""
    mock_provider = MagicMock()

    result = route_text_with_fallback(
        text="Todo buy groceries",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert result.primary_intent == "todo"
    mock_provider.classify.assert_not_called()


def test_route_text_with_fallback_unavailable_llm():
    """Should return regex-only result when LLM is unavailable."""
    mock_provider = MagicMock()
    mock_provider.is_available.return_value = False

    result = route_text_with_fallback(
        text="Some text with no triggers.",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert result.primary_intent is None
    assert result.extracted_intents == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_router.py::test_route_text_with_llm_fallback -v`
Expected: FAIL — `route_text_with_fallback` not defined

- [ ] **Step 3: Implement LLM fallback**

In `src/transcriber/router.py`, add at the top:

```python
import json
```

Add `classify` method expectation comment and the fallback function:

```python
_CLASSIFY_PROMPT = """Analyze this transcript. Return ONLY valid JSON, no other text:
{
  "intents": [{"type": "todo|article_idea|note|blog|none", "content": "extracted text", "position": "start|embedded"}],
  "suggested_tags": ["#tag1", "#tag2"]
}
If no clear intent is detected, return type "none" with empty content.

Transcript:
"""


def route_text_with_fallback(
    text: str,
    intents: list[IntentConfig],
    llm_provider: object | None = None,
) -> RoutingResult:
    """Route text with regex Pass 1, falling back to LLM Pass 2.

    Args:
        text: Transcript text to route.
        intents: Intent definitions for regex matching.
        llm_provider: LLM provider with classify(text) method. If None,
            only regex matching is used.

    Returns:
        RoutingResult with detected intents.
    """
    # Pass 1: regex
    result = route_text(text, intents)

    # If regex found anything, skip LLM
    if result.primary_intent or result.extracted_intents:
        return result

    # Pass 2: LLM fallback
    if llm_provider is None:
        return result

    if not llm_provider.is_available():
        return result

    try:
        prompt = _CLASSIFY_PROMPT + text
        llm_result = llm_provider.classify(prompt)
        data = json.loads(llm_result.stdout)

        suggested_tags = data.get("suggested_tags", [])
        result.tags.extend(suggested_tags)

        for item in data.get("intents", []):
            if item.get("type") == "none":
                continue
            extracted = ExtractedIntent(
                type=item["type"],
                content=item.get("content", ""),
                trigger="llm-fallback",
                position=item.get("position", "embedded"),
                tags=[f"#{item['type']}"],
            )
            if item.get("position") == "start":
                result.primary_intent = item["type"]
            result.extracted_intents.append(extracted)

    except (json.JSONDecodeError, KeyError, AttributeError):
        # LLM returned unparseable output — fail silently, regex result stands
        pass

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_router.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/transcriber/router.py tests/test_router.py
git commit -m "feat: add LLM fallback (Pass 2) to router"
```

---

### Task 11: Integrate router into pipeline

**Files:**
- Modify: `src/transcriber/pipeline.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_pipeline.py`:

```python
def test_pipeline_result_includes_routed():
    """PipelineResult should track routed intent counts."""
    result = PipelineResult(
        processed=3,
        routed=2,
    )
    assert result.routed == 2


def test_pipeline_result_routed_default():
    """PipelineResult.routed should default to 0."""
    result = PipelineResult()
    assert result.routed == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline.py::test_pipeline_result_includes_routed tests/test_pipeline.py::test_pipeline_result_routed_default -v`
Expected: FAIL — `routed` field does not exist

- [ ] **Step 3: Add routed field to PipelineResult**

In `src/transcriber/pipeline.py`, add to `PipelineResult`:

```python
@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    audio_imported: int = 0
    audio_skipped: int = 0
    audio_failed: int = 0
    transcribed: int = 0
    transcribe_failed: int = 0
    processed: int = 0
    process_failed: int = 0
    classified: int = 0
    routed: int = 0

    @property
    def total_successful(self) -> int:
        """Count of fully processed transcripts."""
        return self.processed
```

- [ ] **Step 4: Run new tests to verify they pass**

Run: `pytest tests/test_pipeline.py::test_pipeline_result_includes_routed tests/test_pipeline.py::test_pipeline_result_routed_default -v`
Expected: PASS

- [ ] **Step 5: Add router step to Pipeline.run**

In `src/transcriber/pipeline.py`, add imports at the top:

```python
from datetime import datetime

from transcriber.dispatch import append_to_file, write_intent_file
from transcriber.intents import IntentConfig, load_builtin_intents, load_intents
from transcriber.frontmatter import generate_frontmatter
from transcriber.router import route_text_with_fallback
```

Add a `_route_and_dispatch` method to `Pipeline`:

```python
    def _load_intents(self) -> list[IntentConfig]:
        """Load intent definitions from config or built-in defaults.

        Returns:
            List of IntentConfig.
        """
        if self.config.router.intents_file:
            intents_path = Path(self.config.router.intents_file).expanduser()
            if intents_path.exists():
                return load_intents(intents_path)
        return load_builtin_intents()

    def _route_and_dispatch(self) -> int:
        """Route transcripts through intent detection and dispatch outputs.

        Returns:
            Number of transcripts routed.
        """
        self.console.print("\n[bold]Routing transcripts...[/bold]")

        output_dir = Path(self.config.paths.transcripts)
        base_dir = Path(self.config.paths.base).expanduser()
        intents = self._load_intents()

        # Set up LLM fallback if enabled
        llm_provider = None
        if self.config.router.llm_fallback:
            from transcriber.llm import get_llm_provider
            provider = get_llm_provider(
                self.config.llm.provider,
                self.config.llm.model,
            )
            if provider.is_available():
                llm_provider = provider

        transcript_files = list(output_dir.glob("*.md"))
        if not transcript_files:
            self.console.print("  No transcripts to route")
            return 0

        routed = 0
        for transcript in transcript_files:
            text = transcript.read_text()
            source = transcript.stem.replace("transcript-", "") + ".WAV"
            now = datetime.now()

            result = route_text_with_fallback(text, intents, llm_provider)

            # Run classify for project/tags
            if self.config.classify.enabled and self.config.classify.rules_file:
                rules_path = Path(self.config.classify.rules_file)
                if rules_path.exists():
                    from transcriber.classify import classify_text, load_rules
                    rules = load_rules(rules_path)
                    project, _keyword, classify_tags = classify_text(text, rules)
                    result.project = project
                    result.tags.extend(classify_tags)

            # Merge intent tags into result tags
            for intent in result.extracted_intents:
                result.tags.extend(intent.tags)

            # Deduplicate tags
            seen: set[str] = set()
            unique_tags: list[str] = []
            for tag in result.tags:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            result.tags = unique_tags

            # Add frontmatter to the main transcript
            fm = generate_frontmatter(
                date=now,
                source=source,
                tags=result.tags,
                intent=result.primary_intent,
                project=result.project,
            )
            transcript.write_text(fm + "\n" + text)

            # Dispatch extracted intents
            for intent in result.extracted_intents:
                intent_config = next(
                    (i for i in intents if i.type == intent.type), None
                )
                if not intent_config:
                    continue

                if intent_config.output == "append":
                    target = base_dir / intent_config.target
                    append_to_file(
                        target=target,
                        intent=intent,
                        date=now,
                        source=source,
                        source_transcript=transcript.name if intent.position == "embedded" else None,
                    )
                elif intent_config.output == "file":
                    target_dir = base_dir / intent_config.target
                    write_intent_file(
                        target_dir=target_dir,
                        intent=intent,
                        date=now,
                        source=source,
                        full_text=text,
                        project=result.project,
                    )

                routed += 1

            if result.extracted_intents:
                intent_summary = ", ".join(
                    f"{i.type}" + (f" ({i.person})" if i.person else "")
                    for i in result.extracted_intents
                )
                self.console.print(f"  {transcript.name} -> {intent_summary}")

        self.console.print(f"  Routed: {routed}")
        return routed
```

Update `Pipeline.run` to call the router step after processing, before classify:

```python
    def run(self, skip_import: bool = False) -> PipelineResult:
        result = PipelineResult()

        # Load dictionary for term correction
        dictionary = self._load_dictionary()

        # Step 1: Import audio from DJI device
        if not skip_import:
            imported, skipped, failed = self._import_audio()
            result.audio_imported = imported
            result.audio_skipped = skipped
            result.audio_failed = failed

        # Step 2: Transcribe audio files
        transcribed, transcribe_failed = self._transcribe_audio()
        result.transcribed = transcribed
        result.transcribe_failed = transcribe_failed

        # Step 3: Process transcripts through LLM
        processed, process_failed = self._process_transcripts(dictionary)
        result.processed = processed
        result.process_failed = process_failed

        # Step 4: Route transcripts through intent detection
        result.routed = self._route_and_dispatch()

        # Step 5: Classify transcripts into project directories
        if self.config.classify.enabled:
            result.classified = self._classify_transcripts()

        return result
```

- [ ] **Step 6: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add src/transcriber/pipeline.py tests/test_pipeline.py
git commit -m "feat: integrate router and dispatch into pipeline"
```

---

### Task 12: Update CLI with `--no-llm-fallback` flag

**Files:**
- Modify: `src/transcriber/cli.py:38-99`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_cli.py`:

```python
from typer.testing import CliRunner
from transcriber.cli import app

runner = CliRunner()


def test_cli_process_no_llm_fallback_flag():
    """CLI should accept --no-llm-fallback flag."""
    # Just verify the flag is accepted without error
    result = runner.invoke(app, ["process", "--help"])
    assert "--no-llm-fallback" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_cli_process_no_llm_fallback_flag -v`
Expected: FAIL — `--no-llm-fallback` not in help output

- [ ] **Step 3: Add the flag to CLI**

In `src/transcriber/cli.py`, update the `process` command signature:

```python
@app.command()
def process(
    config_file: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
    skip_import: Annotated[
        bool,
        typer.Option("--skip-import", help="Skip audio import step"),
    ] = False,
    template: Annotated[
        str | None,
        typer.Option("--template", "-t", help="Output template name"),
    ] = None,
    dictionary: Annotated[
        str | None,
        typer.Option("--dictionary", "-d", help="Additional dictionary YAML file"),
    ] = None,
    sort: Annotated[
        bool,
        typer.Option("--sort", help="Auto-classify transcripts into projects"),
    ] = False,
    no_llm_fallback: Annotated[
        bool,
        typer.Option("--no-llm-fallback", help="Disable LLM fallback for intent routing"),
    ] = False,
) -> None:
```

Add after the existing config overrides:

```python
    if no_llm_fallback:
        config.router.llm_fallback = False
```

Add to the pipeline output summary:

```python
    if result.routed:
        console.print(f"  Routed: {result.routed}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::test_cli_process_no_llm_fallback_flag -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/cli.py tests/test_cli.py
git commit -m "feat: add --no-llm-fallback CLI flag"
```

---

### Task 13: Add `classify` method to LLM provider

**Files:**
- Modify: `src/transcriber/llm.py`
- Modify: `tests/test_llm.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_llm.py`:

```python
from unittest.mock import MagicMock, patch

from transcriber.llm import OllamaProvider


def test_ollama_classify_sends_prompt():
    """classify() should send the prompt to ollama and return result."""
    provider = OllamaProvider(model="transcriber:latest")

    mock_result = MagicMock()
    mock_result.stdout = '{"intents": [], "suggested_tags": []}'
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch("shutil.which", return_value="/usr/bin/ollama"):
            result = provider.classify("Analyze this text")

    assert result.stdout == '{"intents": [], "suggested_tags": []}'
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["ollama", "run", "transcriber:latest"]
    assert call_args[1]["input"] == "Analyze this text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py::test_ollama_classify_sends_prompt -v`
Expected: FAIL — `OllamaProvider` has no `classify` method

- [ ] **Step 3: Add classify method**

In `src/transcriber/llm.py`, add to `OllamaProvider`:

```python
    def classify(self, prompt: str) -> subprocess.CompletedProcess[str]:
        """Send a classification prompt to ollama.

        Args:
            prompt: The classification prompt text.

        Returns:
            CompletedProcess with stdout containing the LLM response.
        """
        return subprocess.run(
            ["ollama", "run", self.model],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm.py::test_ollama_classify_sends_prompt -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/transcriber/llm.py tests/test_llm.py
git commit -m "feat: add classify method to OllamaProvider for LLM fallback"
```

---

### Task 14: Update pyproject.toml and add builtin_intents to package

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update pyproject.toml to include builtin_intents.yaml**

In `pyproject.toml`, add the intents file to the force-include section:

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/transcriber/builtin_templates" = "transcriber/builtin_templates"
"src/transcriber/builtin_intents.yaml" = "transcriber/builtin_intents.yaml"
```

- [ ] **Step 2: Verify the file exists**

Run: `ls -la src/transcriber/builtin_intents.yaml`
Expected: File exists (created in Task 3)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: include builtin_intents.yaml in package build"
```

---

### Task 15: End-to-end integration test

**Files:**
- Modify: `tests/test_e2e.py`

- [ ] **Step 1: Write E2E test for intent routing**

Add to `tests/test_e2e.py`:

```python
def test_router_dispatches_todo_to_file(tmp_path: Path) -> None:
    """Router should extract a todo and append it to todos.md."""
    from datetime import datetime
    from transcriber.dispatch import append_to_file
    from transcriber.intents import load_intents
    from transcriber.router import route_text

    # Create intents config
    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: todo
    triggers:
      - "todo"
    output: append
    target: "todos.md"
  - type: todo
    triggers:
      - "speak to {person} about"
    output: append
    target: "todos.md"
    extract:
      person: frontmatter
""")
    intents = load_intents(intents_file)

    # Route a transcript with a start trigger
    result = route_text("Todo watch the Nvidia keynote especially the OpenClaw bit", intents)
    assert result.primary_intent == "todo"
    assert len(result.extracted_intents) == 1

    # Dispatch the intent
    todos_file = tmp_path / "todos.md"
    intent = result.extracted_intents[0]
    append_to_file(
        target=todos_file,
        intent=intent,
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
    )

    content = todos_file.read_text()
    assert "- [ ]" in content
    assert "Nvidia keynote" in content
    assert "DJI_0042.WAV" in content


def test_router_extracts_embedded_intents(tmp_path: Path) -> None:
    """Router should extract embedded todos from a brain dump."""
    from datetime import datetime
    from transcriber.dispatch import append_to_file
    from transcriber.intents import load_intents
    from transcriber.router import route_text

    intents_file = tmp_path / "intents.yaml"
    intents_file.write_text("""
intents:
  - type: todo
    triggers:
      - "todo"
      - "reminder"
    output: append
    target: "todos.md"
  - type: article_idea
    triggers:
      - "article idea"
    output: file
    target: "article-ideas/"
""")
    intents = load_intents(intents_file)

    text = (
        "Article idea about voice-first productivity tools. "
        "They let you capture thoughts on the go. "
        "Todo check out the latest whisper models. "
        "Reminder to update the blog."
    )
    result = route_text(text, intents)

    assert result.primary_intent == "article_idea"
    # Should find the start trigger + 2 embedded todos
    assert len(result.extracted_intents) >= 3

    # Dispatch todos
    todos_file = tmp_path / "todos.md"
    for intent in result.extracted_intents:
        if intent.type == "todo":
            append_to_file(
                target=todos_file,
                intent=intent,
                date=datetime(2026, 3, 30, 14, 32),
                source="DJI_0042.WAV",
                source_transcript="transcript-DJI_0042.md",
            )

    content = todos_file.read_text()
    assert "whisper models" in content.lower()
    assert "update the blog" in content.lower()


def test_frontmatter_on_transcript(tmp_path: Path) -> None:
    """Full transcript should get frontmatter with tags."""
    from datetime import datetime
    from transcriber.frontmatter import generate_frontmatter

    fm = generate_frontmatter(
        date=datetime(2026, 3, 30, 14, 32),
        source="DJI_0042.WAV",
        tags=["#article_idea", "#summit_lab", "#ai"],
        intent="article_idea",
        project="summit-lab",
    )

    transcript_text = "This is my transcript about the summit lab."
    full_output = fm + "\n" + transcript_text

    assert full_output.startswith("---\n")
    assert "#article_idea" in full_output
    assert "summit-lab" in full_output
    assert transcript_text in full_output
```

- [ ] **Step 2: Run E2E tests**

Run: `pytest tests/test_e2e.py::test_router_dispatches_todo_to_file tests/test_e2e.py::test_router_extracts_embedded_intents tests/test_e2e.py::test_frontmatter_on_transcript -v`
Expected: All PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add E2E tests for intent routing and dispatch"
```

---

## Summary

| Task | Description | New/Modified Files |
|------|------------|-------------------|
| 1 | PathsConfig `.processing/` migration | config.py, test_config.py, test_e2e.py |
| 2 | RouterConfig | config.py, test_config.py |
| 3 | Intent config loading | intents.py, builtin_intents.yaml, test_intents.py |
| 4 | Router Pass 1 simple triggers | router.py, test_router.py |
| 5 | Router {person} extraction | router.py, test_router.py |
| 6 | Router embedded intent extraction | router.py, test_router.py |
| 7 | Frontmatter module | frontmatter.py, test_frontmatter.py |
| 8 | Dispatch module | dispatch.py, test_dispatch.py |
| 9 | Classify tags | classify.py, test_classify.py |
| 10 | LLM fallback (Pass 2) | router.py, test_router.py |
| 11 | Pipeline integration | pipeline.py, test_pipeline.py |
| 12 | CLI flag | cli.py, test_cli.py |
| 13 | LLM classify method | llm.py, test_llm.py |
| 14 | Package build config | pyproject.toml |
| 15 | E2E integration tests | test_e2e.py |

**Dependency note:** Task 13 (LLM classify method) should be completed before Task 11 (Pipeline integration), since the pipeline's `_route_and_dispatch` method calls `provider.classify()`. Tasks 1-10 can be done in order. Then 13 → 11 → 12 → 14 → 15.
