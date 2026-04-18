# LLM Model Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve transcript formatting quality by fixing ANSI output artifacts, adding a built-in domain dictionary, creating new Modelfiles with a revised system prompt for three models (gemma4, qwen3.5, llama3.3), and adding a `transcriber models` CLI subcommand.

**Architecture:** The changes span four areas: (1) a one-line fix in `llm.py` to strip ANSI escapes from Ollama output, (2) a new `load_builtin_dictionaries()` function in `dictionary.py` with auto-loading in the pipeline, (3) three new Modelfiles sharing an identical revised system prompt in `src/transcriber/builtin_modelfiles/`, and (4) a new `models` Typer subcommand in `cli.py`. Each area is independent and testable on its own.

**Tech Stack:** Python 3.13, Typer, Rich, PyYAML, Ollama CLI, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/transcriber/llm.py` | Modify | Strip ANSI escape sequences from Ollama stdout |
| `src/transcriber/dictionary.py` | Modify | Add `load_builtin_dictionaries()` function |
| `src/transcriber/pipeline.py` | Modify | Always load built-in dictionary, merge with user dictionaries |
| `src/transcriber/cli.py` | Modify | Add `models` and `models_create` subcommands |
| `src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml` | Create | Domain-specific term corrections |
| `src/transcriber/builtin_modelfiles/gemma4-transcriber.Modelfile` | Create | Modelfile for gemma4:26b |
| `src/transcriber/builtin_modelfiles/qwen3.5-transcriber.Modelfile` | Create | Modelfile for qwen3.5:35b-a3b |
| `src/transcriber/builtin_modelfiles/llama3.3-transcriber.Modelfile` | Create | Modelfile for llama3.3:70b |
| `pyproject.toml` | Modify | Include new builtin directories in wheel build |
| `tests/test_llm.py` | Modify | Add ANSI stripping tests |
| `tests/test_dictionary.py` | Modify | Add builtin dictionary loading tests |
| `tests/test_cli.py` | Modify | Add models subcommand tests |

---

### Task 1: Strip ANSI Escape Sequences from Ollama Output

**Files:**
- Modify: `src/transcriber/llm.py`
- Modify: `tests/test_llm.py`

- [ ] **Step 1: Write failing tests for ANSI stripping**

Add to `tests/test_llm.py`:

```python
from unittest.mock import MagicMock, patch
import subprocess

from transcriber.llm import OllamaProvider


def test_ollama_process_strips_ansi_escapes(tmp_path):
    """process() should strip ANSI escape sequences from Ollama output."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("Raw transcript text.")
    output_file = tmp_path / "output.md"

    ansi_output = "The desired outcomes\x1b[1D\x1b[K\nare completely different\x1b[3D\x1b[K"
    expected_clean = "The desired outcomes\nare completely different"

    mock_result = MagicMock()
    mock_result.stdout = ansi_output
    mock_result.returncode = 0

    provider = OllamaProvider(model="test-model")

    with patch("subprocess.run", return_value=mock_result):
        result = provider.process(input_file, output_file)

    assert result.success
    content = output_file.read_text()
    assert "\x1b" not in content
    assert content == expected_clean


def test_ollama_classify_strips_ansi_escapes():
    """classify() should strip ANSI escape sequences from Ollama output."""
    ansi_output = '{"intent": "todo"}\x1b[1D\x1b[K'

    mock_result = MagicMock()
    mock_result.stdout = ansi_output
    mock_result.returncode = 0

    provider = OllamaProvider(model="test-model")

    with patch("subprocess.run", return_value=mock_result):
        result = provider.classify("Analyze this text")

    assert "\x1b" not in result.stdout
    assert result.stdout == '{"intent": "todo"}'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_llm.py::test_ollama_process_strips_ansi_escapes tests/test_llm.py::test_ollama_classify_strips_ansi_escapes -v`
Expected: FAIL — ANSI sequences still present in output

- [ ] **Step 3: Implement ANSI stripping in OllamaProvider**

Edit `src/transcriber/llm.py`. Add the `re` import at the top (it's not currently imported) and a module-level constant:

```python
import re

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
```

In the `process()` method, after `subprocess.run()` returns and before writing the output file, strip the escapes. Replace the line:

```python
            output_file.write_text(result.stdout)
```

with:

```python
            cleaned = ANSI_ESCAPE.sub('', result.stdout)
            output_file.write_text(cleaned)
```

In the `classify()` method, strip escapes before returning. Replace:

```python
        return subprocess.run(
            ["ollama", "run", self.model],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )
```

with:

```python
        result = subprocess.run(
            ["ollama", "run", self.model],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )
        result.stdout = ANSI_ESCAPE.sub('', result.stdout)
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_llm.py -v`
Expected: All tests PASS (including existing ones)

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -v`
Expected: All 118+ tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/llm.py tests/test_llm.py
git commit -m "fix: strip ANSI escape sequences from Ollama output"
```

---

### Task 2: Create Built-in Dictionary YAML

**Files:**
- Create: `src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml`

- [ ] **Step 1: Create the builtin_dictionaries directory and YAML file**

Create `src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml`:

```yaml
corrections:
  # Red Hat products
  - wrong: "open shift"
    right: "OpenShift"
  - wrong: "auto mission hub"
    right: "Automation Hub"
  - wrong: "auto mission controller"
    right: "automation controller"
  - wrong: "auto mission mesh"
    right: "automation mesh"
  - wrong: "ansible automation platform"
    right: "Ansible Automation Platform"

  # Ansible terms
  - wrong: "play book"
    right: "playbook"
  - wrong: "play books"
    right: "playbooks"

  # AI/ML tools
  - wrong: "open claw"
    right: "OpenClaw"
  - wrong: "nano claw"
    right: "NanoClaw"
  - wrong: "lang chain"
    right: "LangChain"
  - wrong: "lang graph"
    right: "LangGraph"
  - wrong: "deep agents"
    right: "Deep Agents"
  - wrong: "llama stack"
    right: "Llama Stack"
  - wrong: "v llm"
    right: "vLLM"
  - wrong: "VLLM"
    right: "vLLM"

  # Infrastructure
  - wrong: "cube control"
    right: "kubectl"
  - wrong: "cube cuddle"
    right: "kubectl"
  - wrong: "cube CTL"
    right: "kubectl"
  - wrong: "cube C T L"
    right: "kubectl"
  - wrong: "helm chart"
    right: "Helm chart"
```

- [ ] **Step 2: Verify the YAML is valid**

Run: `uv run python -c "import yaml; yaml.safe_load(open('src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml'))"`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/transcriber/builtin_dictionaries/redhat-ecosystem.yaml
git commit -m "feat: add built-in Red Hat ecosystem dictionary"
```

---

### Task 3: Add Built-in Dictionary Loading

**Files:**
- Modify: `src/transcriber/dictionary.py`
- Modify: `src/transcriber/pipeline.py`
- Modify: `tests/test_dictionary.py`

- [ ] **Step 1: Write failing tests for builtin dictionary loading**

Add to `tests/test_dictionary.py`:

```python
from transcriber.dictionary import load_builtin_dictionaries


def test_load_builtin_dictionaries():
    """Should load the built-in Red Hat ecosystem dictionary."""
    d = load_builtin_dictionaries()
    assert len(d.corrections) > 0
    assert d.apply("I used open claw for the demo.") == "I used OpenClaw for the demo."


def test_load_builtin_dictionaries_includes_key_terms():
    """Built-in dictionary should include essential domain terms."""
    d = load_builtin_dictionaries()
    assert "OpenShift" in d.apply("We deployed on open shift.")
    assert "LangChain" in d.apply("I used lang chain.")
    assert "kubectl" in d.apply("Run cube control get pods.")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_dictionary.py::test_load_builtin_dictionaries tests/test_dictionary.py::test_load_builtin_dictionaries_includes_key_terms -v`
Expected: FAIL — `load_builtin_dictionaries` not defined

- [ ] **Step 3: Implement load_builtin_dictionaries in dictionary.py**

Add to `src/transcriber/dictionary.py`, following the same pattern as `intents.py`:

```python
BUILTIN_DICTIONARY_DIR = Path(__file__).parent / "builtin_dictionaries"


def load_builtin_dictionaries() -> Dictionary:
    """Load built-in dictionaries shipped with the package.

    Returns:
        Dictionary with all built-in corrections merged.
    """
    paths = find_dictionaries([BUILTIN_DICTIONARY_DIR])
    return load_dictionaries(paths)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dictionary.py -v`
Expected: All tests PASS

- [ ] **Step 5: Update pipeline to always load built-in dictionary**

Edit `src/transcriber/pipeline.py`. Update the import line:

```python
from transcriber.dictionary import Dictionary, load_builtin_dictionaries, load_dictionaries
```

Replace the `_load_dictionary` method:

```python
    def _load_dictionary(self) -> Dictionary:
        """Load term correction dictionaries.

        Always loads built-in dictionaries. User-configured dictionaries
        are merged on top.

        Returns:
            Merged Dictionary from built-in and configured paths.
        """
        builtin = load_builtin_dictionaries()
        user_paths = [Path(p) for p in self.config.dictionaries.paths]
        if user_paths:
            user_dict = load_dictionaries(user_paths)
            combined = Dictionary(corrections=builtin.corrections + user_dict.corrections)
        else:
            combined = builtin

        if combined.corrections:
            self.console.print(
                f"  Loaded {len(combined.corrections)} term corrections"
            )
        return combined
```

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/transcriber/dictionary.py src/transcriber/pipeline.py tests/test_dictionary.py
git commit -m "feat: auto-load built-in dictionaries in pipeline"
```

---

### Task 4: Create Modelfiles with Revised System Prompt

**Files:**
- Create: `src/transcriber/builtin_modelfiles/gemma4-transcriber.Modelfile`
- Create: `src/transcriber/builtin_modelfiles/qwen3.5-transcriber.Modelfile`
- Create: `src/transcriber/builtin_modelfiles/llama3.3-transcriber.Modelfile`

- [ ] **Step 1: Create the builtin_modelfiles directory**

Run: `mkdir -p src/transcriber/builtin_modelfiles`

- [ ] **Step 2: Create the gemma4 Modelfile**

Create `src/transcriber/builtin_modelfiles/gemma4-transcriber.Modelfile`:

```
FROM gemma4:26b

SYSTEM """You are a text formatter for a solutions architect at Red Hat who records voice notes about Ansible, Kubernetes, AI/ML, and internal projects using a DJI MIC 2.

Your task: transform raw speech-to-text output into well-structured, readable markdown.

## Rules

1. Preserve the original meaning and all substantive content
2. Break content into logical paragraphs (2-4 sentences each)
3. Use markdown headings (## for main sections, ### for subsections) when topics shift
4. Use **bold** for key terms and `code blocks` for commands, filenames, or code
5. Correct obvious speech-to-text errors for technical terms (see domain terms below)
6. Maintain the speaker's voice, tone, and first-person perspective
7. Output clean markdown only — no preamble, no trailing summary, no metadata header

## Never do these

- Never add [was: original-word] correction markers
- Never append a raw transcript reference section
- Never add a metadata block (date, source, word count) at the top
- Never output ANSI escape sequences or terminal control characters
- Never remove or paraphrase the speaker's words beyond fixing clear STT errors
- Never switch from first-person to third-person voice

## Domain terms

When the speaker discusses these topics, use the correct spelling:

**Red Hat ecosystem:** Ansible Automation Platform (AAP), OpenShift, Advanced Cluster Management (ACM), RHEL, Automation Hub, execution environments, automation controller, automation mesh, playbook, role, collection, inventory

**AI/ML tools:** OpenClaw, NanoClaw, Ollama, LangChain, LangGraph, Deep Agents, Llama Stack, RAG, vLLM, LLM-D, Hugging Face, PyTorch

**Infrastructure:** Kubernetes, kubectl, Helm, Podman, Bitwarden, CI/CD, GitHub, GitLab

## Structure

- Short content (<100 words): just clean up and add paragraph breaks
- Medium content (100-300 words): paragraphs with optional headings
- Long content (>300 words): clear heading hierarchy with logical sections

Output only the formatted text with no preamble or explanation."""

PARAMETER temperature 0.1
PARAMETER top_p 0.9
```

- [ ] **Step 3: Create the qwen3.5 Modelfile**

Create `src/transcriber/builtin_modelfiles/qwen3.5-transcriber.Modelfile` with identical content except the first line:

```
FROM qwen3.5:35b-a3b
```

All other content (SYSTEM prompt, PARAMETER lines) is identical to the gemma4 Modelfile.

- [ ] **Step 4: Create the llama3.3 Modelfile**

Create `src/transcriber/builtin_modelfiles/llama3.3-transcriber.Modelfile` with identical content except the first line:

```
FROM llama3.3:70b
```

All other content (SYSTEM prompt, PARAMETER lines) is identical to the gemma4 Modelfile.

- [ ] **Step 5: Verify all three Modelfiles exist and have correct base models**

Run: `head -1 src/transcriber/builtin_modelfiles/*.Modelfile`
Expected:
```
==> gemma4-transcriber.Modelfile <==
FROM gemma4:26b
==> llama3.3-transcriber.Modelfile <==
FROM llama3.3:70b
==> qwen3.5-transcriber.Modelfile <==
FROM qwen3.5:35b-a3b
```

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/builtin_modelfiles/
git commit -m "feat: add Modelfiles for gemma4, qwen3.5, llama3.3 with revised prompt"
```

---

### Task 5: Add `transcriber models` CLI Subcommand

**Files:**
- Modify: `src/transcriber/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for the models subcommand**

Add to `tests/test_cli.py`:

```python
from unittest.mock import patch, MagicMock


def test_cli_models_command_exists():
    """CLI should have a models command that lists available Modelfiles."""
    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "gemma4" in result.output
    assert "qwen3.5" in result.output
    assert "llama3.3" in result.output


def test_cli_models_create_help():
    """models create should show help with available model names."""
    result = runner.invoke(app, ["models-create", "--help"])
    assert result.exit_code == 0
    assert "name" in result.output.lower()


def test_cli_models_create_invalid_name():
    """models create should reject unknown model names."""
    result = runner.invoke(app, ["models-create", "nonexistent"])
    assert result.exit_code != 0 or "not found" in result.output.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py::test_cli_models_command_exists tests/test_cli.py::test_cli_models_create_help tests/test_cli.py::test_cli_models_create_invalid_name -v`
Expected: FAIL — no `models` command

- [ ] **Step 3: Implement the models subcommands in cli.py**

Add to `src/transcriber/cli.py`, after the `templates` command:

```python
BUILTIN_MODELFILE_DIR = Path(__file__).parent / "builtin_modelfiles"


@app.command()
def models() -> None:
    """List available Modelfiles for Ollama."""
    import shutil
    import subprocess

    if not BUILTIN_MODELFILE_DIR.is_dir():
        console.print("[red]No built-in Modelfiles found.[/red]")
        raise typer.Exit(1)

    modelfiles = sorted(BUILTIN_MODELFILE_DIR.glob("*.Modelfile"))
    if not modelfiles:
        console.print("[red]No Modelfiles found.[/red]")
        raise typer.Exit(1)

    # Check which Ollama models exist
    existing_models: set[str] = set()
    if shutil.which("ollama"):
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.splitlines():
                if line.strip():
                    existing_models.add(line.split()[0])
        except subprocess.CalledProcessError:
            pass

    console.print("[bold]Available Modelfiles:[/bold]")
    for mf in modelfiles:
        name = mf.stem.replace("-transcriber", "")
        ollama_name = f"transcriber-{name}:latest"
        status = "[green]created[/green]" if ollama_name in existing_models else "[dim]not created[/dim]"
        base_model = ""
        for line in mf.read_text().splitlines():
            if line.startswith("FROM "):
                base_model = line[5:].strip()
                break
        console.print(f"  {name:12s} base={base_model:20s} {status}")

    console.print(f"\nCreate with: [bold]transcriber models-create <name>[/bold]")


@app.command(name="models-create")
def models_create(
    name: Annotated[
        str,
        typer.Argument(help="Model name (e.g., gemma4, qwen3.5, llama3.3)"),
    ],
) -> None:
    """Create an Ollama model from a built-in Modelfile."""
    import subprocess

    modelfile = BUILTIN_MODELFILE_DIR / f"{name}-transcriber.Modelfile"
    if not modelfile.exists():
        available = [
            f.stem.replace("-transcriber", "")
            for f in sorted(BUILTIN_MODELFILE_DIR.glob("*.Modelfile"))
        ]
        console.print(f"[red]Modelfile not found: {name}[/red]")
        console.print(f"Available: {', '.join(available)}")
        raise typer.Exit(1)

    ollama_name = f"transcriber-{name}"
    console.print(f"Creating Ollama model [bold]{ollama_name}[/bold] from {modelfile.name}...")

    try:
        subprocess.run(
            ["ollama", "create", ollama_name, "-f", str(modelfile)],
            check=True,
        )
        console.print(f"[green]Model {ollama_name}:latest created successfully.[/green]")
        console.print(f"\nTo use: set [bold]model = \"{ollama_name}:latest\"[/bold] in config.toml")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to create model: {e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[red]ollama not found. Install from https://ollama.com[/red]")
        raise typer.Exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/cli.py tests/test_cli.py
git commit -m "feat: add transcriber models and models-create CLI commands"
```

---

### Task 6: Update Package Build Configuration

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add builtin_dictionaries and builtin_modelfiles to wheel build**

Edit `pyproject.toml`. Add two new lines to the `[tool.hatch.build.targets.wheel.force-include]` section:

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/transcriber/builtin_templates" = "transcriber/builtin_templates"
"src/transcriber/builtin_intents.yaml" = "transcriber/builtin_intents.yaml"
"src/transcriber/builtin_dictionaries" = "transcriber/builtin_dictionaries"
"src/transcriber/builtin_modelfiles" = "transcriber/builtin_modelfiles"
```

- [ ] **Step 2: Verify the package builds correctly**

Run: `uv run python -c "from transcriber.dictionary import load_builtin_dictionaries; d = load_builtin_dictionaries(); print(f'{len(d.corrections)} corrections loaded')"`
Expected: `22 corrections loaded` (or current count)

- [ ] **Step 3: Verify Modelfiles are accessible**

Run: `uv run python -c "from pathlib import Path; d = Path('src/transcriber/builtin_modelfiles'); print([f.name for f in sorted(d.glob('*.Modelfile'))])"`
Expected: `['gemma4-transcriber.Modelfile', 'llama3.3-transcriber.Modelfile', 'qwen3.5-transcriber.Modelfile']`

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "chore: include builtin dictionaries and Modelfiles in package build"
```

---

### Task 7: Integration Smoke Test

**Files:** None — manual verification

- [ ] **Step 1: Verify the full pipeline dictionary integration**

Run: `uv run python -c "
from transcriber.dictionary import load_builtin_dictionaries, load_dictionaries
from pathlib import Path

# Load built-in
builtin = load_builtin_dictionaries()
print(f'Built-in corrections: {len(builtin.corrections)}')

# Test key corrections
tests = [
    ('I used open claw for the demo', 'OpenClaw'),
    ('Deploy on open shift today', 'OpenShift'),
    ('Run cube control get pods', 'kubectl'),
    ('We built a lang chain pipeline', 'LangChain'),
    ('Check the play book syntax', 'playbook'),
]
for text, expected in tests:
    result = builtin.apply(text)
    status = 'PASS' if expected in result else 'FAIL'
    print(f'  {status}: \"{text}\" -> found \"{expected}\"')
"`
Expected: All corrections PASS

- [ ] **Step 2: Verify models CLI**

Run: `uv run transcriber models`
Expected: Lists three Modelfiles with base model info and creation status

- [ ] **Step 3: Verify ANSI stripping works on existing transcripts**

Run: `uv run python -c "
import re
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
from pathlib import Path
transcripts = list(Path.home().glob('Resources/Transcripts/transcripts/*.md'))
for t in transcripts:
    content = t.read_text()
    if ANSI_ESCAPE.search(content):
        print(f'  ANSI found in: {t.name}')
    else:
        print(f'  Clean: {t.name}')
"`
Expected: Shows which existing files still have ANSI (they won't be retroactively fixed — only new runs benefit)

- [ ] **Step 4: Run full test suite one final time**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 5: Commit any remaining changes**

If nothing to commit, skip this step.
