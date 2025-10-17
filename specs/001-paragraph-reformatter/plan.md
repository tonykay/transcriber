# Implementation Plan: Paragraph Reformatter Modelfile

**Branch**: `001-paragraph-reformatter` | **Date**: 2025-10-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-paragraph-reformatter/spec.md`

## Summary

Create a new Ollama Modelfile (`Modelfile-reformat`) that transforms unstructured text from speech-to-text transcriptions into well-organized paragraphs. The model will analyze text for logical topic boundaries and sentence groupings, then output the same content with appropriate paragraph breaks while preserving 100% of the original text. This addresses the need for readable, professionally formatted transcripts from raw ASR output.

## Technical Context

**Language/Version**: Modelfile DSL (Ollama format)
**Primary Dependencies**: Ollama runtime (existing dependency in project)
**Storage**: N/A (stateless text transformation)
**Testing**: Manual validation with sample transcripts, comparison testing (word-for-word preservation)
**Target Platform**: macOS with Ollama installed (existing project platform)
**Project Type**: Configuration file (Modelfile) - no traditional source code structure
**Performance Goals**: Process typical transcripts (500-2000 words) in under 30 seconds
**Constraints**: Must preserve 100% of original content, no additions/deletions/modifications beyond paragraph formatting
**Scale/Scope**: Single Modelfile, handles texts up to ~10,000 words

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance with Core Principles

✅ **I. Pipeline Architecture** - COMPLIANT
- The reformatter integrates as an **optional enhancement tool** within the existing 3-stage pipeline
- Can be used independently or as part of Stage 3 (AI Enhancement)
- Does NOT modify the core pipeline structure (Import → Transcribe → Process)
- Adds capability without disrupting existing workflow

✅ **II. AI-Driven Enhancement** - COMPLIANT
- This Modelfile directly supports the AI-Driven Enhancement principle
- Provides additional formatting capability beyond the existing `transcriber` model
- Configurable via Ollama (aligns with "AI models MUST be configurable")
- Enhances structure and formatting while preserving content (core requirement)

✅ **III. State-Tracked File Processing** - COMPLIANT
- Modelfile is stateless - does not modify file processing logic
- Integrates with existing directory structure without changes
- No impact on file movement or state tracking

✅ **IV. CLI-First Interface** - COMPLIANT
- Accessible via Ollama CLI: `ollama run transcriber-reformat < input.txt`
- Can be invoked from bash scripts (existing `transcriber.sh`)
- Maintains CLI-first approach

✅ **V. Error Resilience** - COMPLIANT
- Ollama handles model errors gracefully (existing dependency)
- No changes to batch processing error handling
- File-level processing continues on failures (existing behavior)

### Additional Constraints Compliance

✅ **Naming Conventions** - COMPLIANT
- Modelfile name: `Modelfile-reformat` (follows project pattern)
- Does not affect audio or transcript naming conventions

✅ **Dependency Management** - COMPLIANT
- Uses existing Ollama dependency (already required for `transcriber` model)
- No new external dependencies added

✅ **File System Structure** - COMPLIANT
- Modelfile stored in `Modelfiles/` directory (existing location)
- No changes to `~/Resources/Transcripts/` structure

**GATE STATUS**: ✅ PASS - No constitution violations. Feature is a simple addition that enhances existing AI capabilities without modifying core architecture.

## Project Structure

### Documentation (this feature)

```
specs/001-paragraph-reformatter/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (model prompt engineering best practices)
├── quickstart.md        # Phase 1 output (usage examples)
└── checklists/
    └── requirements.md  # Specification quality checklist (completed)
```

### Source Code (repository root)

```
Modelfiles/
├── Modelfile            # Existing transcriber model
└── Modelfile-reformat   # NEW: Paragraph reformatter model (this feature)
```

**Structure Decision**: Simple configuration file addition. No source code directories needed. The Modelfile will be placed in the existing `Modelfiles/` directory alongside the current `Modelfile` for the transcriber model. Testing will be manual validation with sample transcripts.

## Complexity Tracking

*No constitution violations to track - all checks passed.*
