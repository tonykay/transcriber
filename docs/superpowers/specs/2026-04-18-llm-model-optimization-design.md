# LLM Model Optimization & Output Quality — Design Spec

**Date**: 2026-04-18
**Status**: Draft
**Scope**: Improve transcript formatting quality, reduce model memory footprint, fix output artifacts

## Problem Statement

The current transcription pipeline uses `llama3.3:70b` (42GB on disk, ~102GB in memory) for text reformatting. On a 128GB machine this crowds out other applications. Additionally:

1. **Output artifacts**: ANSI terminal escape sequences (`ESC[1D`, `ESC[K`) leak into formatted transcripts from Ollama's progressive rendering. These appear as `[1D[K` in the final markdown files.
2. **Term misrecognition**: The STT step (Parakeet) consistently misrecognizes domain-specific terms (Red Hat ecosystem, AI/ML tooling, project codenames). The current Modelfile system prompt has a generic tech term list that doesn't cover the user's actual vocabulary.
3. **Prompt bloat**: The 140-line system prompt includes instructions for `[was: original-word]` correction markers, raw transcript appendices, and metadata headers that produce unwanted output.

## Design

### 1. Revised System Prompt

Replace the current Modelfile system prompt with a shorter, clearer prompt structured in three sections:

**Role & context**: Ground the model in the user's domain — a solutions architect at Red Hat who records voice notes about Ansible, Kubernetes, AI/ML, and internal projects. This gives the model implicit context for term disambiguation without listing every possible term.

**Formatting rules**:
- Break content into logical paragraphs (2-4 sentences)
- Use markdown headings (`##`, `###`) for topic shifts
- Use `**bold**` for key terms, `code blocks` for commands/filenames
- Output clean markdown only — no preamble, no trailing summary
- Never output `[was:]` correction markers
- Never append the raw transcript
- Never output a metadata header block
- Never output ANSI escape sequences or control characters

**Domain term guidance**: A curated list of the user's actual ecosystem terms, organized by category:

- **Red Hat**: Ansible Automation Platform (AAP), OpenShift, Advanced Cluster Management (ACM), RHEL, Automation Hub, execution environments
- **Ansible**: playbook, role, collection, inventory, automation controller, automation mesh
- **AI/ML tools**: OpenClaw, NanoClaw, Ollama, LangChain, LangGraph, Deep Agents, Llama Stack, RAG, vLLM, LLM-D
- **Infrastructure**: Kubernetes, kubectl, Helm, Bitwarden, Podman

**Parameters**:
- `temperature 0.1` — maximum determinism for content preservation
- `top_p 0.9` — controlled randomness
- No `repeat_penalty` — newer models handle repetition natively

### 2. ANSI Escape Sequence Fix

**Root cause**: `ollama run` performs progressive terminal rendering — printing partial tokens, then using cursor-movement and erase escape sequences to overwrite them. When captured via `subprocess.run(..., capture_output=True)`, these raw bytes are included in stdout.

**Source**: Confirmed that Parakeet's STT output is clean. The escape sequences originate exclusively from the Ollama LLM step.

**Fix**: In `llm.py`, strip ANSI control sequences from captured stdout before writing to the output file:

```python
import re
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
cleaned = ANSI_ESCAPE.sub('', result.stdout)
```

Applied in `OllamaProvider.process()` after `subprocess.run()` returns, before writing `output_file`. Also applied in `OllamaProvider.classify()` for consistency.

### 3. Built-in Dictionary

**Purpose**: Deterministic post-LLM correction for known STT misrecognitions. The dictionary runs after the model has done its contextual reformatting, catching any terms the model missed or got wrong.

**Location**: `src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml`

**Loading**: The pipeline auto-loads the built-in dictionary (similar to `builtin_intents.yaml`). User-specified dictionaries via `--dictionary` flag or config layer on top. The built-in dictionary is always active with no config required.

**Content categories**:

- **Red Hat products**: "open shift" -> "OpenShift", "ansible automation platform" -> "Ansible Automation Platform", "auto mission hub" -> "Automation Hub"
- **AI/ML tools**: "open claw" -> "OpenClaw", "nano claw" -> "NanoClaw", "lang chain" -> "LangChain", "lang graph" -> "LangGraph", "deep agents" -> "Deep Agents", "llama stack" -> "Llama Stack", "v llm" -> "vLLM"
- **Infrastructure**: "cube control" -> "kubectl", "cube cuddle" -> "kubectl", "cube CTL" -> "kubectl"
- **Ansible terms**: "play book" -> "playbook", "auto mission controller" -> "automation controller"

**Design principle**: Conservative — only include corrections where we're confident the substitution is always correct. Ambiguous terms (where context matters) belong in the system prompt, not the dictionary.

### 4. Modelfiles & CLI

**Modelfile location**: `src/transcriber/builtin_modelfiles/` directory, shipped with the package.

Three Modelfiles sharing the identical new system prompt, differing only in base model:

| File | Base Model | Size | Notes |
|------|-----------|------|-------|
| `gemma4-transcriber.Modelfile` | `gemma4:26b` | 17GB | Google's latest, strong instruction following |
| `qwen3.5-transcriber.Modelfile` | `qwen3.5:35b-a3b` | 23GB | MoE, 35B total / 3B active, fast inference |
| `llama3.3-transcriber.Modelfile` | `llama3.3:70b` | 42GB | Current baseline with updated prompt |

**CLI subcommand**: `transcriber models`

- `transcriber models` — lists available Modelfiles and shows which corresponding Ollama models exist
- `transcriber models create <name>` — runs `ollama create` with the matching Modelfile (e.g., `transcriber models create gemma4` creates `transcriber-gemma4:latest`)

**Config**: The `[llm] model` setting in `config.toml` points at whichever Ollama model the user wants (e.g., `model = "transcriber-gemma4:latest"`). The default in `config.py` remains `transcriber:latest` for backwards compatibility.

### 5. Model Bake-off (Manual)

After implementation, the user will:

1. Create all three Ollama models via `transcriber models create gemma4`, etc.
2. Run each against the same raw transcript (e.g., `2026-04-18-09-22-49.txt`)
3. Compare output quality, term accuracy, and speed
4. Set their preferred model in config

This is a manual evaluation step, not automated in the pipeline.

## Files Changed

| File | Change |
|------|--------|
| `src/transcriber/llm.py` | Strip ANSI escapes from Ollama stdout |
| `src/transcriber/pipeline.py` | Auto-load built-in dictionary |
| `src/transcriber/dictionary.py` | Add `load_builtin_dictionaries()` function |
| `src/transcriber/cli.py` | Add `transcriber models` subcommand |
| `src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml` | New: built-in term corrections |
| `src/transcriber/builtin_modelfiles/gemma4-transcriber.Modelfile` | New: gemma4 Modelfile |
| `src/transcriber/builtin_modelfiles/qwen3.5-transcriber.Modelfile` | New: qwen3.5 Modelfile |
| `src/transcriber/builtin_modelfiles/llama3.3-transcriber.Modelfile` | New: llama3.3 Modelfile |
| `Modelfiles/` | Preserved as legacy reference |
| `pyproject.toml` | Include new builtin directories in package build |
| `tests/` | New tests for ANSI stripping, dictionary loading, models CLI |

## Not Changing

- Parakeet STT step (output is clean)
- Template system
- Intent routing / dispatch
- Frontmatter generation
- Pipeline flow / step ordering
- Existing user-facing CLI commands
