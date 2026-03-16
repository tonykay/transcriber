# CLAUDE.md - Development Context

## Project Overview

**Transcriber** - A Python-based voice capture and processing system for turning DJI audio recordings into structured, classified documents.

### Vision

A voice-first personal capture system that:
- Transcribes audio recordings with high accuracy
- Corrects technical terminology via customizable dictionaries
- Formats output using templates (reports, blogs, notes, etc.)
- Auto-classifies and sorts transcripts into project directories
- Integrates with Claude CLI for AI-powered processing

## Architecture

```
transcriber/
├── src/transcriber/          # Core library
│   ├── __init__.py
│   ├── audio.py              # Audio import, file handling
│   ├── transcribe.py         # Speech-to-text (Parakeet MLX)
│   ├── process.py            # Text processing pipeline
│   ├── dictionary.py         # Term correction (LangChain, etc.)
│   ├── templates.py          # Output formatting (Jinja2)
│   ├── classify.py           # Auto-sorting and classification
│   └── config.py             # Configuration management
├── cli/
│   └── main.py               # CLI entry point (Click/Typer)
├── templates/                # Output templates
│   ├── default.md
│   ├── blog.md
│   ├── trip-report.md
│   └── summary.md
├── dictionaries/             # Term correction dictionaries
│   └── tech-terms.yaml       # e.g., "Long Chain" → "LangChain"
├── config/
│   └── default.toml          # Default configuration
├── legacy/
│   └── transcriber-bash.sh   # Original Bash implementation
├── tests/
└── pyproject.toml
```

### Design Principles

- **Library + CLI**: Core logic as importable modules, thin CLI wrapper
- **Pipeline architecture**: Each step is independent and composable
- **Configuration-driven**: Paths, models, behaviors via config files
- **Extensible**: Easy to add new templates, dictionaries, classifiers

## CLI Interface (Planned)

```bash
# Basic usage - process all pending audio
transcriber

# With options
transcriber --output summary,full          # Multiple output formats
transcriber --template blog                 # Apply specific template
transcriber --sort                          # Auto-classify into projects
transcriber --dictionary custom-terms.yaml  # Custom term corrections

# Subcommands
transcriber process                         # Run full pipeline
transcriber classify <file>                 # Classify a specific transcript
transcriber reformat <file> --template X    # Reformat existing transcript
transcriber config --show                   # Show current configuration
```

## Core Features

### 1. Term Correction (Dictionary)
- YAML-based dictionaries mapping misheard terms to correct spellings
- Fuzzy matching for common speech-to-text errors
- Domain-specific dictionaries (tech, medical, project-specific)

### 2. Templates
- Jinja2-based output templates
- Built-in templates: default, blog, trip-report, summary
- Custom templates in `~/.config/transcriber/templates/`

### 3. Auto-Classification
- Keyword/pattern matching for project detection
- Directory-based organization: `~/Transcripts/projects/<project>/`
- Fallback `misc/` category for unclassified items
- Future: tagging system (#work, #idea, #event)

### 4. Configuration
- TOML config files
- Hierarchy: defaults → user config → CLI flags
- Configurable: paths, models, default template, sort behavior

## Dependencies

- **parakeet-mlx**: Speech-to-text (Apple Silicon optimized)
- **ollama**: Local LLM for text enhancement
- **claude CLI**: AI processing integration
- **click** or **typer**: CLI framework
- **jinja2**: Template rendering
- **pyyaml**: Dictionary files
- **tomli/tomllib**: Config files

## Directory Structure (Runtime)

```
~/Resources/Transcripts/           # Or configured location
├── inbox/                         # Incoming audio
├── processing/                    # Work in progress
├── projects/                      # Classified transcripts
│   ├── project-a/
│   ├── project-b/
│   └── misc/                      # Unclassified
├── archive/                       # Processed audio
└── logs/                          # Processing logs
```

## Current Status

- **Branch**: `002-python-rewrite`
- **Phase**: Design and planning
- **Legacy**: Bash implementation preserved in `legacy/transcriber-bash.sh`

### Completed
- ✅ Original Bash pipeline (working, in legacy/)
- ✅ Paragraph reformatter Ollama model
- ✅ Architecture design

### In Progress
- 🔄 Python project structure
- 🔄 Core library implementation

### Planned
- 📋 Term correction system
- 📋 Template system
- 📋 Auto-classification
- 📋 Configuration management
- 📋 CLI implementation

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run CLI during development
python -m transcriber.cli

# Type checking
mypy src/

# Legacy bash script (still works)
./legacy/transcriber-bash.sh
```

## Future Directions

- **Quick capture**: Short thoughts/ideas logged and easily searchable
- **Todo integration**: Voice notes that update task lists
- **Tagging system**: #event #work #idea markers
- **Manual sort UI**: Fallback interface for classification failures
- **Claude Skills integration**: Programmatic access to Skills
