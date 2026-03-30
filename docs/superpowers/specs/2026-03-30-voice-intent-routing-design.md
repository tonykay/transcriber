# Voice Intent Routing & Smart Capture

**Date:** 2026-03-30
**Branch:** 002-python-rewrite
**Status:** Design approved

## Overview

Evolve Transcriber from "transcribe and file" to "understand and route." Add intent detection to voice recordings so the system can identify what a recording *is* (todo, article idea, blog draft, note) and route it accordingly — appending to lists, filing to directories, or both.

## Goals

- Detect explicit voice triggers ("Todo", "Article Idea", "Speak to John about") in transcripts
- Extract quick-capture items (todos, notes) and append to dedicated files
- File multi-session artifacts (article ideas, blog drafts) as individual files in dedicated directories
- Add YAML frontmatter with tags to all outputs for Obsidian compatibility
- Extract embedded intents from long brain-dump recordings
- Provide LLM fallback classification when no explicit triggers are found

## Architecture: Two-Pass Hybrid Router

### Pass 1: Regex-based trigger matching (fast, deterministic)

Scans transcript text for trigger phrases defined in `intents.yaml`. Handles 90%+ of cases where the speaker gives explicit guidance.

### Pass 2: LLM-assisted classification (fallback only)

Fires only when Pass 1 finds no triggers. Sends transcript to existing Ollama provider with a classification prompt. Returns structured JSON with detected intents and suggested tags.

## Intent Types & Trigger Patterns

### Built-in Intent Types

| Intent | Trigger Phrases | Output Mode | Target |
|--------|----------------|-------------|--------|
| `todo` | "Todo", "To do", "Reminder" | Append | `todos.md` |
| `todo` (person) | "Speak to {person} about", "Talk to {person} about", "Ask {person} about", "Tell {person} about" | Append | `todos.md` (with `assigned:` field) |
| `article_idea` | "Article idea", "Blog idea", "Writing idea" | File | `article-ideas/` |
| `note` | "Note", "Quick note" | Append | `notes.md` |
| `blog` | "Blog post", "Blog draft" | File | `blogs/` |

### Trigger Config File (`intents.yaml`)

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
      person: frontmatter  # adds assigned: {person}

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

### Detection Rules

- Triggers matched **case-insensitively** against transcript text
- Trigger at the **start** of transcript sets primary intent for the whole recording
- Triggers found **mid-text** extract just that sentence/phrase as a quick-capture item (embedded intents)
- Trigger phrase stripped from extracted content
- `{person}` is a named capture group — extracts word(s) until a stop word ("about", "regarding", "that")
- Word boundary matching to avoid false positives (e.g. "want to do" should not match "to do")

## Router Module

### Data structures

```python
@dataclass
class ExtractedIntent:
    type: str           # "todo", "article_idea", "note", "blog"
    content: str        # The extracted text, trigger stripped
    trigger: str        # The trigger phrase that matched
    person: str | None  # Extracted person name, if applicable
    position: str       # "start" (whole-recording intent) or "embedded"
    tags: list[str]     # Auto-generated tags, prefixed with #

@dataclass
class RoutingResult:
    primary_intent: str | None        # Intent from start-of-recording trigger
    extracted_intents: list[ExtractedIntent]  # All intents found (including embedded)
    project: str | None               # From existing classify system
    tags: list[str]                   # Merged tags from all sources, prefixed with #
    full_text: str                    # Original transcript text
```

### Pipeline integration

```
audio -> STT -> LLM formatting -> router -> dispatch
                                    |
                    +---------------+----------------+
                    |               |                |
              full transcript   todos.md    article-ideas/
              with frontmatter  (append)    (individual files)
              filed to project/
```

The router slots in after LLM formatting, before file output. It does not modify the transcript text — it reads it and produces routing decisions.

## Embedded Intent Extraction

During a brain dump, trigger phrases anywhere in the text are detected and extracted.

Example input:
> "...and we should really show the GitOps workflow. Oh, todo, ask James about the cluster quota limits. Anyway, back to the demo flow..."

Result:
- Full transcript filed normally (with frontmatter)
- Todo extracted: "Ask James about the cluster quota limits" appended to `todos.md`

### Boundary detection for embedded intents

Content extraction ends at:
1. **Sentence boundary** — next `. ! ?` punctuation
2. **Next trigger** — another trigger phrase terminates the previous extraction
3. **Paragraph boundary** — paragraph break terminates extraction

### Edge cases

- **Multiple embedded intents** — all extracted, each appended/filed separately
- **Start trigger + embedded triggers** — both fire independently
- **Trigger as substring** — word boundary matching prevents false positives

## Tag Generation & Frontmatter

### Tag sources

1. **Intent type** — detected intent becomes a tag (`#todo`, `#article_idea`)
2. **Project classification** — matched project becomes a tag (`#summit_lab`)
3. **Keyword extraction** — classify keywords that match become tags (`#ai`, `#kubernetes`)
4. **Person names** — extracted from "speak to {person}" patterns (`#john`)

### Tag format

- Prefixed with `#`
- Lowercase with underscores for spaces (`#claude_code`, `#article_idea`)
- Deduplicated

### Frontmatter format (full transcripts and file-mode intents)

```yaml
---
date: 2026-03-30T14:32:00
source: DJI_0042.WAV
tags: ["#article_idea", "#summit_lab", "#ai", "#agentic"]
intent: article_idea
project: summit-lab
---

The actual transcript content here...
```

### Append format (todos, notes)

```markdown
- [ ] Watch the Nvidia keynote, especially the OpenClaw bit
  `2026-03-30 14:32 | DJI_0042.WAV | #nvidia #ai`

- [ ] Ask James about the cluster quota limits
  `2026-03-30 14:32 | DJI_0042.WAV | #james #summit_lab`
  Assigned: James
  *Extracted from: transcript-DJI_0042.md*
```

The `Extracted from:` line appears on embedded intents to link back to the full transcript for context.

## LLM Fallback (Pass 2)

When Pass 1 finds no triggers, the transcript is sent to the LLM with:

```
Analyze this transcript. Return JSON:
{
  "intents": [{"type": "todo|article_idea|note|blog|none", "content": "...", "position": "start|embedded"}],
  "suggested_tags": ["#tag1", "#tag2"]
}
If no clear intent is detected, return type "none" with empty intents.
```

- Uses existing Ollama provider infrastructure
- Suggested tags merged with project classification tags
- Intent type `none` means normal pipeline flow — frontmatter and classification only

## Directory Structure

### Revised layout

```
~/Resources/Transcripts/
├── .processing/              # Hidden — all intermediate artifacts
│   ├── audio-unprocessed/
│   ├── audio-processed/
│   ├── text-unprocessed/
│   └── text-processed/
├── transcripts/              # Full formatted transcripts with frontmatter
├── projects/                 # Classified transcripts by project
│   ├── summit-lab/
│   ├── kubecon/
│   └── misc/
├── todos.md                  # Appended checklist
├── notes.md                  # Appended quick notes
├── article-ideas/            # Each idea = individual file
│   ├── 2026-03-30-nvidia-openclaw.md
│   └── 2026-03-28-voice-capture-workflow.md
└── blogs/                    # Blog-intent full transcripts
    ├── 2026-03-29-agentic-devops.md
    └── 2026-03-30-agentic-devops.md
```

### Key decisions

- `.processing/` hides intermediate files — implementation details, not browsable outputs
- Top-level capture files (`todos.md`, `notes.md`) are directly visible for quick access
- `article-ideas/` and `blogs/` are directories — multi-session artifacts get individual files
- Obsidian-ready: point a vault at this directory and everything works (`.processing/` hidden by default)

### Config change

`PathsConfig` derives intermediate paths from `.processing/` subdirectory:

```python
@property
def audio_unprocessed(self) -> str:
    return str(Path(self.base).expanduser() / ".processing" / "audio-unprocessed")
```

## Module Changes

| File | Change |
|------|--------|
| `src/transcriber/router.py` | **New** — intent detection, extraction, dispatch |
| `src/transcriber/frontmatter.py` | **New** — YAML frontmatter generation |
| `src/transcriber/config.py` | **Modified** — add `RouterConfig`, update `PathsConfig` for `.processing/` |
| `src/transcriber/pipeline.py` | **Modified** — insert router step after LLM processing |
| `src/transcriber/classify.py` | **Modified** — return tags alongside project name |
| `src/transcriber/cli.py` | **Modified** — add `--no-llm-fallback` flag |
| `intents.yaml` | **New** — default intent trigger definitions |
| `tests/test_router.py` | **New** — router unit tests |
| `tests/test_frontmatter.py` | **New** — frontmatter generation tests |

### Unchanged modules

- `audio.py` — untouched
- `stt.py` — untouched
- `llm.py` — untouched (LLM fallback instantiates an `OllamaProvider` directly from `router.py` with a classification-specific prompt, no changes to `llm.py` needed)
- `dictionary.py` — untouched
- `templates.py` — untouched (frontmatter handled by new module)

## Future Considerations (not in scope)

- External integrations (Apple Reminders, Todoist, GitHub Issues)
- Obsidian vault direct integration
- Tagging UI for manual classification
- Todo completion tracking
- Cross-reference linking between related recordings
