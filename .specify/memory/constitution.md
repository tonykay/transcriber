# DJI Transcriber Constitution

<!--
SYNC IMPACT REPORT
==================
Version: 0.0.0 → 1.0.0 (Initial constitution)
Rationale: MAJOR version - Initial establishment of core principles and governance

Changes:
- ✅ NEW: Core principle I - Pipeline Architecture
- ✅ NEW: Core principle II - AI-Driven Enhancement
- ✅ NEW: Core principle III - State-Tracked File Processing
- ✅ NEW: Core principle IV - CLI-First Interface
- ✅ NEW: Core principle V - Error Resilience
- ✅ NEW: Additional Constraints section
- ✅ NEW: Development Workflow section
- ✅ NEW: Governance section

Template Updates:
- ✅ plan-template.md: Constitution Check section already aligned
- ✅ spec-template.md: Requirements structure supports pipeline principles
- ✅ tasks-template.md: Phase structure supports sequential pipeline tasks
- ⚠️  No command files to update (none exist yet)

Follow-up TODOs:
- None - all placeholders filled
-->

## Core Principles

### I. Pipeline Architecture

**Principle**: The transcriber MUST operate as a three-stage sequential pipeline with clear separation between stages.

**Requirements**:
- Stage 1 (Import): Audio file acquisition and timestamp-based renaming
- Stage 2 (Transcribe): Speech-to-text conversion using Parakeet MLX
- Stage 3 (Process): AI-driven transcript enhancement using Ollama
- Each stage MUST complete successfully before the next stage begins
- Pipeline MUST be executable as a complete workflow or individual stages
- Each stage MUST track its input and output directories independently

**Rationale**: Clear stage separation enables debugging, partial processing, recovery from failures, and independent testing of each transformation step. This prevents cascading failures and allows users to restart from any stage.

### II. AI-Driven Enhancement

**Principle**: Raw transcriptions MUST be enhanced through AI models to produce structured, formatted output.

**Requirements**:
- AI enhancement is NOT optional - it is a required pipeline stage
- Enhancement MUST transform raw speech-to-text into structured markdown
- AI models MUST be configurable (currently Ollama with custom `transcriber` model)
- Enhancement MUST preserve original content while improving formatting and structure
- Output MUST be markdown format with clear section hierarchy

**Rationale**: Speech-to-text output is often unformatted, lacks punctuation, and requires interpretation. AI enhancement transforms raw transcripts into professionally formatted, readable documents that capture the speaker's intent and organize content logically.

### III. State-Tracked File Processing

**Principle**: Files MUST move through distinct directories that reflect their processing state, preventing duplicate processing and enabling recovery.

**Requirements**:
- Directory structure MUST reflect processing state:
  - `audio-unprocessed/` → `audio-processed/`
  - `text-unprocessed/` → `text-processed/`
  - Final output: `transcripts/`
- Files MUST be moved (not copied) between state directories after successful processing
- No file MUST be processed more than once (enforced by directory state)
- File naming MUST maintain traceability across all stages
- Processing MUST be idempotent - re-running stages should be safe

**Rationale**: State-tracked directories provide visual progress indication, prevent duplicate work, enable safe interruption and resumption, and create an audit trail of processing history. This is critical for batch processing where failures may occur.

### IV. CLI-First Interface

**Principle**: All functionality MUST be accessible via command-line interface with both script execution and function sourcing modes.

**Requirements**:
- Script MUST be executable as standalone: `./transcriber.sh`
- Functions MUST be sourceable for individual execution: `source transcriber.sh && process_dji_audio`
- Each pipeline stage MUST be callable as an independent function
- Error messages MUST be clear and actionable
- Progress reporting MUST indicate current file and total progress
- Help documentation MUST be accessible via `usage()` function

**Rationale**: CLI-first design enables automation, scripting, integration with other tools, and flexible execution modes. Function sourcing allows developers and power users to execute specific stages for debugging and testing.

### V. Error Resilience

**Principle**: Failures in individual files MUST NOT halt batch processing, and the system MUST provide clear error reporting and recovery paths.

**Requirements**:
- Dependency checking MUST occur before processing (parakeet-mlx, ollama)
- File-level errors MUST be logged but NOT stop batch processing
- Progress reporting MUST include success/failure counts
- Error messages MUST include actionable remediation steps
- File system validation MUST occur before operations (directory existence, permissions)
- Partial processing MUST be recoverable (re-running stages processes only unprocessed files)

**Rationale**: Batch processing of audio recordings often encounters edge cases (corrupted files, missing data, network issues with AI services). Resilient error handling ensures maximum throughput while providing visibility into failures for later remediation.

## Additional Constraints

### Naming Conventions (NON-NEGOTIABLE)

**DJI Import Format**:
- Input: `DJI_XX_YYYYMMDD_HHMMSS.WAV` (from DJI device)
- Output: `YYYY-MM-DD-HH:MM:SS.WAV` (ISO 8601 timestamp format)
- Rationale: ISO timestamps ensure chronological sorting, human readability, and international compatibility

**Transcript Naming**:
- Format: `transcript-YYYY-MM-DD-HH:MM:SS.md`
- Rationale: Prefix enables filtering, timestamp maintains traceability to source audio

### Dependency Management

**External Tools**:
- Parakeet MLX (speech-to-text): MUST be installed and accessible in PATH
- Ollama (AI runtime): MUST be installed with custom `transcriber` model
- Bash 4.0+: Required for modern array handling and regex features

**Hardware Requirements**:
- Mac with Apple Silicon: Recommended for Parakeet MLX performance optimization
- DJI Mic 2 or compatible device: Source of audio recordings
- Adequate storage: Required for multi-stage file processing (audio files can be large)

### File System Structure (NON-NEGOTIABLE)

**Base Directory**: `~/Resources/Transcripts/`

**Subdirectory Requirements**:
```
audio-unprocessed/    # Raw audio from DJI device
audio-processed/      # Transcribed audio (archived)
text-unprocessed/     # Raw transcriptions from Parakeet
text-processed/       # AI-processed text (archived)
transcripts/          # Final markdown output (deliverables)
```

**Rationale**: Consistent directory structure enables automation, prevents confusion, and provides clear visual indication of processing state. The `~/Resources/` location separates user content from application code.

## Development Workflow

### Testing Requirements

**Manual Testing**:
- MUST test complete pipeline with sample DJI audio files
- MUST verify each stage can be executed independently
- MUST test error handling with invalid/missing dependencies
- MUST validate output formatting and markdown structure

**Test Cases**:
- Empty input directories (no files to process)
- Invalid file formats
- Missing dependencies (parakeet-mlx, ollama)
- Interrupted processing (partial completion)
- Duplicate file handling
- Timestamp parsing edge cases

### Code Quality Standards

**Bash Script Requirements**:
- Functions MUST have descriptive names matching their purpose
- Error messages MUST be informative and actionable
- Regex patterns MUST be documented with examples
- File operations MUST validate paths before execution
- Exit codes MUST be used appropriately (0=success, non-zero=failure)

**Documentation Requirements**:
- Inline comments for complex logic (especially regex)
- Function documentation describing purpose, inputs, outputs
- Usage examples in help text
- README.md with complete setup and usage instructions

### Commit Standards

**Commit Messages**:
- Use conventional commits format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Example: `feat(transcribe): add batch processing support`

**Commit Scope**:
- Commit after completing functional changes to individual stages
- Do NOT commit broken/incomplete pipeline stages
- Include documentation updates in the same commit as code changes

## Governance

### Amendment Process

**Amendment Requirements**:
- Constitution changes MUST be documented with version bumps
- Changes MUST include rationale and affected principles
- Template synchronization MUST be verified after amendments
- Version numbering follows semantic versioning:
  - MAJOR: Breaking changes to principles, removed principles, incompatible governance changes
  - MINOR: New principles added, expanded guidance, new sections
  - PATCH: Clarifications, wording improvements, non-semantic fixes

### Compliance Verification

**Every feature/change MUST**:
- Verify compliance with pipeline architecture (3 stages, clear separation)
- Verify state-tracked file processing (correct directory movements)
- Verify CLI-first interface (both execution modes work)
- Verify error resilience (batch processing continues on individual failures)
- Verify AI enhancement is preserved (do not bypass Stage 3)

**Review Checklist**:
- [ ] Does the change maintain the three-stage pipeline?
- [ ] Are files correctly moved between state directories?
- [ ] Can the feature be executed via both script and sourced functions?
- [ ] Does error handling allow batch processing to continue?
- [ ] Are dependency checks performed before processing?
- [ ] Is the naming convention maintained?
- [ ] Are error messages actionable?

### Complexity Justification

**When to justify complexity**:
- Adding additional pipeline stages beyond the three defined stages
- Introducing new file state directories beyond the five defined
- Adding new external dependencies beyond Parakeet MLX and Ollama
- Creating configuration files (constitution prefers convention over configuration)

**Justification Requirements**:
- Document the specific problem being solved
- Explain why simpler alternatives are insufficient
- Demonstrate alignment with core principles
- Provide migration path if breaking existing workflows

### Versioning and History

**Version**: 1.0.0
**Ratified**: 2025-10-16
**Last Amended**: 2025-10-16

**Version History**:
- 1.0.0 (2025-10-16): Initial constitution ratified with five core principles and governance structure
