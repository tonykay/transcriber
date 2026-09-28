# Handoff: Output Directory CLI Options
Date: 2026-09-17T01:39:29Z (local: 09-16 19:39) | Branch: main | Status: ready for review

## Summary
The session investigated Transcriber's architecture and implemented two CLI features: a per-run output workspace override and a read-only listing of built-in output destinations. The feature is committed as `c170779` and pushed to `origin/main`; all 137 tests passed. Unrelated pre-existing edits remain in the working tree and must be preserved.

## Work Completed
- [x] Verified current source rather than relying on recalled branch/test counts. Memory described an older `002-python-rewrite` branch; actual work was on `main`.
- [x] Added `transcriber process --output-dir PATH` / `-o PATH`. It overrides `config.paths.base` after loading configuration, without persisting the change.
- [x] Added eager top-level `transcriber --list-output-dirs`, which prints built-in defaults and exits without loading user configuration, running the pipeline, or creating directories.
- [x] Listed append targets (`todos.md`, `notes.md`) separately as files, rather than misrepresenting them as directories. Intent targets are loaded from built-in YAML and deduplicated.
- [x] Added five tests covering overrides, config precedence, relative paths and home expansion, unchanged behavior without the flag, listing side effects, and help text.
- [x] Added user documentation and a rendered session summary.
- [x] Ran tests, changed-file lint, repository type checking, and an actual CLI listing.
- [x] Committed only the feature's three files. Temporarily stashed unrelated tracked edits for pull/rebase, pushed, then restored the stash. The temporary stash was dropped successfully.

## Files Affected
- Modified: `src/transcriber/cli.py:27` — `list_output_dirs_callback`; top-level option in `main`; `--output-dir/-o` in `process`; base override before pipeline construction.
- Created: `tests/test_cli_output.py` — five CLI tests using a mocked pipeline, not real Ollama/STT.
- Created: `docs/output-directories.md` — usage, override scope, config precedence, and default layout.
- Created locally: `.pi/artifacts/transcriber-output-directory-options-diff-and-usage.html` — rendered summary, not part of feature commit.
- Created locally: this handoff. A duplicate earlier draft was removed; this is the sole session handoff.
- Deleted: none.

## Technical Context
### Architecture
Transcriber converts DJI audio into Obsidian-compatible Markdown: import → STT (primarily Parakeet MLX) → Ollama formatting → dictionary corrections and Jinja2 templates → intent routing and dispatch → optional project classification.

`src/transcriber/config.py:8` defines `PathsConfig`. `base` defaults to `~/Resources/Transcripts`; properties derive `transcripts/` and `.processing/{audio,text}-{unprocessed,processed}/`. `pipeline.py` derives intent targets and `projects/` from the same base. Thus updating one field propagates the override without pipeline edits.

The intent loader is `src/transcriber/intents.py`, backed by `src/transcriber/builtin_intents.yaml`. Built-in targets are `todos.md`, `notes.md`, `article-ideas/`, and `blogs/`. Relative targets follow the base; custom absolute targets do not.

### Decisions and scope
- Treated “output directory” as the entire workspace, including intermediates, not only final Markdown. This assumption was stated during the session; no additional confirmation was obtained.
- Reused `[paths].base` rather than introducing another config field or separate per-destination CLI flags. This was the smallest change supported by current architecture; there was no need to refactor dispatch.
- Listing means **built-in defaults**, not effective user-configured destinations. `transcriber config` already displays the configured base, but does not provide a complete destination listing.
- Config selection: explicit `--config`, otherwise `./transcriber.toml`, otherwise `~/.config/transcriber/config.toml`, otherwise defaults. The new process flag overrides the loaded base only for that invocation.
- `Path.expanduser()` expands home paths; relative paths remain relative to the working directory. The flag does not move existing data, change DJI source, or write config.
- With `--skip-import`, pending inputs must already be inside the selected workspace. `reprocess` and `classify` did not gain an output override; use `[paths].base` in their config.
- Rich output uses `markup=False` for literal paths and `soft_wrap=True` for long paths. Listing tests use a wide terminal to accommodate temporary paths.
- No dependencies or config schema changes.

## Current State
- Working: both flags, existing CLI behavior, and full test suite. The pipeline was mocked in new tests; no real audio/Ollama run was performed for this change.
- Tests: `uv run pytest -q` → **137 passed**. Changed-file Ruff check → **All checks passed!**
- Known issues: `uv run mypy src/` exits 1 with six errors in unchanged modules; no errors reported in `cli.py`:

```text
src/transcriber/intents.py:6: error: Library stubs not installed for "yaml" [import-untyped]
src/transcriber/dictionary.py:7: error: Library stubs not installed for "yaml" [import-untyped]
src/transcriber/router.py:321: error: "object" has no attribute "is_available" [attr-defined]
src/transcriber/router.py:326: error: "object" has no attribute "classify" [attr-defined]
src/transcriber/classify.py:7: error: Library stubs not installed for "yaml" [import-untyped]
src/transcriber/templates.py:63: error: Missing type parameters for generic type "dict" [type-arg]
Found 6 errors in 5 files (checked 14 source files)
```

### Git snapshot before handoff
`main` was up to date with `origin/main`. The push included the 17 already-local commits plus this feature commit. Unrelated changes were not committed:

```text
## main...origin/main
 M AGENTS.md
 T CLAUDE.md
 M README.md
 M src/transcriber/llm.py
 M tests/test_llm.py
?? .agents/
?? .github/
?? .pi/
?? graphify-out/
?? openwiki/
?? src/transcriber/builtin_modelfiles/muse-transcriber.Modelfile
```

Recent commits captured before writing:

```text
c170779 feat: add --output-dir override and --list-output-dirs CLI options
3bc0ae3 fix: catch subprocess errors in LLM intent classification fallback
9ba4d7a fix: increase Ollama process() timeout from 5 to 15 minutes
d1ecabb feat: add date tags (#transcript #yyyy #yyyy-mm) to all templates
f0999ea fix: add timeouts to Ollama subprocess calls
af13fc0 feat: add transcriber reprocess command for re-running LLM on a single file
f24bf8a fix: disable thinking mode in gemma4 and qwen3.5 Modelfiles
e8e6127 refactor: address code review findings
a9cf63e fix: replace colons with hyphens in transcript filenames for Obsidian compatibility
65bdede style: fix line length and unnecessary f-string in models CLI
```

## Next Steps
### Immediate
1. Read `docs/output-directories.md:1` and inspect `git show c170779 -- src/transcriber/cli.py tests/test_cli_output.py docs/output-directories.md` to review the delivered scope. No outstanding implementation is required.
2. Run `git status --short --branch` before editing; preserve the unrelated changes listed above. Ask the user what to work on next rather than treating those changes as unfinished work from this feature.

### Then
- If requested, add README discoverability for the new options, carefully preserving existing README edits.
- If users need effective/configured destination listings or overrides on `reprocess`/`classify`, clarify those semantics before extending the CLI. They were not implemented here.
- Address the existing mypy debt only as a separately scoped task.

### Blocked on
- Nothing for the completed feature. Further enhancements require user direction.

## Useful Commands & Resources
Run from `/Users/tok/Dropbox/PARAL/Projects/transcriber-home/transcriber`:

```bash
uv run pytest -q
uv run pytest tests/test_cli_output.py -q
uv run ruff check src/transcriber/cli.py tests/test_cli_output.py
uv run mypy src/
uv run transcriber --list-output-dirs
uv run transcriber process --help
uv run transcriber config
```

Actual processing examples (these run the pipeline, not a dry run):

```bash
uv run transcriber process --output-dir ~/Resources/OtherTranscripts
uv run transcriber process -o "./meeting notes" --skip-import
```

- Remote: `https://github.com/tonykay/transcriber.git`
- Feature documentation: `docs/output-directories.md`
- Source of path defaults: `src/transcriber/config.py`
- Intent destinations: `src/transcriber/builtin_intents.yaml`
- Hindsight contains the single-base design and new flag semantics; verify recalled claims against source. Use bank `claude-code-global` per project instructions.
