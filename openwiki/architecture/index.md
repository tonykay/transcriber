# Files

- [Runtime Files, Metadata, and Mutation Boundaries](runtime-file-lifecycle.md) - Documents the configurable on-disk workspace used to import, transcribe, format, route, and optionally project-sort DJI recordings. Explains generated Markdown metadata and exactly where runtime operations move, append, overwrite, or copy user data.
- [System Architecture and Ownership Boundaries](system-overview.md) - Describes the installed Transcriber CLI, orchestration pipeline, provider seams, content services, and filesystem-backed workspace. Use it to identify the correct change boundary for ingestion, model integration, routing, formatting, or output behavior.
