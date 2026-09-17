# Output directories

Choose a workspace for one pipeline run:

```bash
transcriber process --output-dir ~/Resources/OtherTranscripts
transcriber process -o "./meeting notes"
```

`--output-dir` overrides `[paths].base` from the loaded configuration for this run only.
It relocates final transcripts, built-in intent outputs, classified projects, and
`.processing` intermediates together. It does not move existing recordings or outputs,
change the DJI source, or save the override to your configuration. With `--skip-import`,
the pipeline looks for pending work in the selected workspace.
Custom absolute intent targets remain absolute rather than moving under the new base.

For a permanent default (also used by `reprocess` and `classify`), set:

```toml
[paths]
base = "~/Resources/OtherTranscripts"
```

Pass a particular config with `transcriber process --config path/to/config.toml`.
Otherwise the CLI checks `./transcriber.toml`, then
`~/.config/transcriber/config.toml`, then uses built-in defaults.

## List built-in defaults

```bash
transcriber --list-output-dirs
```

This read-only flag ignores user configuration and exits without starting the
pipeline or creating directories. It lists expanded paths under the built-in base,
`~/Resources/Transcripts`:

- `transcripts/` — formatted transcripts
- `projects/` — classified transcripts, when classification is enabled
- `article-ideas/` and `blogs/` — individual intent documents
- `todos.md` and `notes.md` — append targets, labeled separately as files
- `.processing/audio-unprocessed/` and `.processing/audio-processed/` — audio intermediates
- `.processing/text-unprocessed/` and `.processing/text-processed/` — raw text intermediates

Use `transcriber config` to see your currently configured base rather than the
built-in default.
