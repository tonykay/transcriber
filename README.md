# Transcriber

A Python voice capture and processing system that turns DJI audio recordings into structured, classified markdown documents with smart intent routing.

## What It Does

1. **Imports** audio files from your DJI MIC 2 (or any audio source)
2. **Transcribes** speech to text using Parakeet MLX (Apple Silicon optimized)
3. **Formats** raw transcripts into clean paragraphs via Ollama LLM
4. **Routes** recordings by intent -- detects voice triggers like "Todo", "Article idea", "Speak to John about"
5. **Outputs** Obsidian-compatible markdown with YAML frontmatter and tags

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Parakeet MLX](https://github.com/senstella/parakeet-mlx) for speech-to-text
- [Ollama](https://ollama.com) for LLM processing

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd transcriber

# Install in development mode
uv pip install -e ".[dev]"

# Create the Ollama transcriber model (one-time)
ollama create transcriber -f Modelfile
```

After installation, `transcriber` is available as a command on your PATH.

### Hardware

- **DJI MIC 2** or compatible audio device
- **Mac with Apple Silicon** (recommended for Parakeet MLX)

## Quick Start

```bash
# Plug in your DJI MIC 2, then run:
transcriber process
```

This runs the full pipeline: import, transcribe, format, route, and classify.

## CLI Reference

```bash
# Full pipeline
transcriber process

# Skip audio import (files already copied)
transcriber process --skip-import

# Use a specific template
transcriber process --template blog

# Add a custom dictionary for term correction
transcriber process --dictionary my-terms.yaml

# Auto-classify into project directories
transcriber process --sort

# Disable LLM fallback (regex-only intent routing)
transcriber process --no-llm-fallback

# Classify a single transcript
transcriber classify transcript.md --rules rules.yaml

# Reformat with a different template
transcriber reformat transcript.md --template summary

# Show current configuration
transcriber config

# List available templates
transcriber templates

# Show version
transcriber --version
```

## Intent Routing

Transcriber detects voice triggers in your recordings and routes them automatically:

| You say... | What happens |
|------------|-------------|
| "Todo, review the PR" | Appended to `todos.md` |
| "Speak to John about KubeCon" | Appended to `todos.md` with `Assigned: John` |
| "Article idea, voice-first productivity" | Individual file in `article-ideas/` |
| "Blog post, why agentic DevOps matters" | Individual file in `blogs/` |
| "Note, remember to check the logs" | Appended to `notes.md` |

Triggers work at the start of a recording (sets the whole file's intent) or **mid-sentence** during a longer brain dump -- embedded todos get extracted automatically.

When no explicit trigger is detected, an optional LLM fallback classifies the recording semantically.

### Custom Triggers

Define your own triggers in `~/.config/transcriber/intents.yaml`:

```yaml
intents:
  - type: todo
    triggers:
      - "todo"
      - "reminder"
    output: append
    target: "todos.md"
```

## Output Format

All outputs include YAML frontmatter for Obsidian compatibility:

```yaml
---
date: 2026-03-30T14:32:00
source: DJI_0042.WAV
tags: ["#article_idea", "#summit_lab", "#ai"]
intent: article_idea
project: summit-lab
---

Your transcript content here...
```

## Directory Structure

```
~/Resources/Transcripts/
├── .processing/              # Hidden intermediate files
│   ├── audio-unprocessed/
│   ├── audio-processed/
│   ├── text-unprocessed/
│   └── text-processed/
├── transcripts/              # Full formatted transcripts
├── projects/                 # Classified by project
│   ├── summit-lab/
│   └── misc/
├── todos.md                  # Captured todos
├── notes.md                  # Quick notes
├── article-ideas/            # Article idea recordings
└── blogs/                    # Blog draft recordings
```

## Configuration

Transcriber looks for config in this order:
1. `./transcriber.toml` (current directory)
2. `~/.config/transcriber/config.toml`
3. Built-in defaults

```toml
[paths]
base = "~/Resources/Transcripts"
dji_source = "/Volumes/DJI_MIC2"

[stt]
provider = "parakeet"    # or "whisper"

[llm]
provider = "ollama"
model = "transcriber:latest"

[output]
template = "default.md"

[router]
llm_fallback = true
# intents_file = "~/.config/transcriber/intents.yaml"

[classify]
enabled = false
# rules_file = "~/.config/transcriber/rules.yaml"
```

## Templates

Built-in templates: `default.md`, `blog.md`, `trip-report.md`, `summary.md`

Add custom templates to `~/.config/transcriber/templates/`.

## Development

```bash
# Run tests (118 tests)
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Run CLI during development (without installing)
uv run transcriber process
```

## Architecture

```
src/transcriber/
├── cli.py              # CLI entry point (Typer + Rich)
├── config.py           # Configuration (Pydantic V2, TOML)
├── pipeline.py         # Pipeline orchestration
├── audio.py            # DJI audio import
├── stt.py              # Speech-to-text (Parakeet provider)
├── llm.py              # LLM processing (Ollama provider)
├── dictionary.py       # Term correction (YAML dictionaries)
├── templates.py        # Output formatting (Jinja2)
├── router.py           # Intent detection (regex + LLM fallback)
├── intents.py          # Intent config loading
├── frontmatter.py      # YAML frontmatter generation
├── dispatch.py         # Output routing (append/file)
├── classify.py         # Project classification
├── builtin_intents.yaml
└── builtin_templates/
    ├── default.md
    ├── blog.md
    ├── trip-report.md
    └── summary.md
```

## Legacy

The original Bash implementation is preserved in `legacy/transcriber-bash.sh`.
