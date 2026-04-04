# CLAUDE.md - Development Context

## Project Overview

**Transcriber** - A Python-based voice capture and processing system for turning DJI audio recordings into structured, classified documents with smart intent routing.

### Vision

A voice-first personal capture system that:
- Transcribes audio recordings with high accuracy
- Detects voice triggers and routes recordings by intent (todo, article idea, note, blog)
- Extracts embedded actionable items from brain-dump recordings
- Corrects technical terminology via customizable dictionaries
- Formats output using templates with Obsidian-compatible frontmatter
- Auto-classifies and sorts transcripts into project directories

## Architecture

```
src/transcriber/
├── cli.py              # CLI entry point (Typer + Rich)
├── config.py           # Configuration (Pydantic V2, TOML)
├── pipeline.py         # Pipeline orchestration
├── audio.py            # DJI audio import, file handling
├── stt.py              # Speech-to-text (Parakeet provider)
├── llm.py              # LLM processing (Ollama provider)
├── dictionary.py       # Term correction (YAML dictionaries)
├── templates.py        # Output formatting (Jinja2)
├── router.py           # Two-pass intent detection (regex + LLM fallback)
├── intents.py          # Intent config loading from YAML
├── frontmatter.py      # YAML frontmatter generation
├── dispatch.py         # Output routing (append to file / individual files)
├── classify.py         # Project classification (keyword matching)
├── builtin_intents.yaml # Default intent trigger definitions
└── builtin_templates/   # Built-in output templates
    ├── default.md
    ├── blog.md
    ├── trip-report.md
    └── summary.md
```

### Design Principles

- **Library + CLI**: Core logic as importable modules, thin CLI wrapper
- **Pipeline architecture**: Each step is independent and composable
- **Configuration-driven**: Paths, models, behaviors via TOML config files
- **Two-pass routing**: Fast regex for explicit triggers, LLM fallback for ambiguous content
- **Obsidian-ready**: YAML frontmatter with #tags on all outputs

## CLI Interface

```bash
# Full pipeline
transcriber process

# With options
transcriber process --template blog
transcriber process --sort
transcriber process --dictionary custom-terms.yaml
transcriber process --skip-import
transcriber process --no-llm-fallback

# Subcommands
transcriber classify <file>         # Classify a specific transcript
transcriber reformat <file> -t X    # Reformat with a template
transcriber config                  # Show current configuration
transcriber templates               # List available templates
```

## Core Features

### 1. Intent Routing (Router)
- Explicit voice triggers: "Todo", "Article idea", "Speak to {person} about"
- Embedded intent extraction from long brain-dump recordings
- Two-pass: regex matching (Pass 1) + LLM classification fallback (Pass 2)
- Configurable triggers via `intents.yaml`

### 2. Output Dispatch
- **Append mode**: Todos and notes appended to `todos.md`, `notes.md`
- **File mode**: Article ideas and blogs as individual files in dedicated directories
- Person extraction: "Speak to John about X" -> `Assigned: John`

### 3. Frontmatter & Tags
- YAML frontmatter on all outputs (date, source, tags, intent, project)
- Tags prefixed with `#`, underscored: `#claude_code`, `#article_idea`
- Obsidian-compatible format

### 4. Term Correction (Dictionary)
- YAML-based dictionaries mapping misheard terms to correct spellings
- Domain-specific dictionaries (tech, project-specific)

### 5. Templates
- Jinja2-based output templates
- Built-in: default, blog, trip-report, summary
- Custom templates in `~/.config/transcriber/templates/`

### 6. Auto-Classification
- Keyword/pattern matching for project detection
- Directory-based organization with tags
- Fallback `misc/` category for unclassified items

### 7. Configuration
- TOML config files (Pydantic V2 models)
- Hierarchy: defaults -> user config -> CLI flags

## Dependencies

- **parakeet-mlx**: Speech-to-text (Apple Silicon optimized)
- **ollama**: Local LLM for text enhancement and classification fallback
- **typer**: CLI framework
- **rich**: Terminal output formatting
- **pydantic**: Configuration models (V2)
- **jinja2**: Template rendering
- **pyyaml**: Dictionary and intent config files

## Directory Structure (Runtime)

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
├── todos.md                  # Appended todos
├── notes.md                  # Appended notes
├── article-ideas/            # Individual article idea files
└── blogs/                    # Individual blog draft files
```

## Current Status

- **Phase**: Feature-complete, pending real-world testing
- **Legacy**: Original Bash implementation preserved in `legacy/transcriber-bash.sh`

### Completed
- Audio import module (DJI file handling)
- Speech-to-text module (Parakeet provider)
- LLM processing module (Ollama provider)
- Pipeline orchestration
- CLI implementation (Typer + Rich)
- Configuration management (Pydantic V2, TOML)
- Term correction system (YAML dictionaries)
- Template system (Jinja2, 4 built-in templates)
- Auto-classification (keyword matching, project sorting)
- Intent routing (two-pass: regex + LLM fallback)
- Person extraction from triggers
- Embedded intent extraction from brain dumps
- Frontmatter generation (Obsidian-compatible)
- Output dispatch (append + file modes)
- Full test suite (118 tests)

## Development Commands

```bash
# Install in development mode
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run CLI during development
uv run transcriber process

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

## Design Docs

- `docs/superpowers/specs/2026-03-30-voice-intent-routing-design.md` - Intent routing spec
- `docs/superpowers/plans/2026-03-30-voice-intent-routing.md` - Implementation plan

## Future Directions

- External integrations (Apple Reminders, Todoist, GitHub Issues)
- Direct Obsidian vault integration
- Smaller/faster model for LLM classification fallback
- Quick capture mode for short voice notes
- Tagging UI for manual classification failures
- Cross-reference linking between related recordings
