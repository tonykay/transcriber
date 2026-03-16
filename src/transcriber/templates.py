"""Output formatting using Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


# Built-in templates ship with the package
BUILTIN_TEMPLATE_DIR = Path(__file__).parent / "builtin_templates"


def get_template_dirs(extra_dirs: list[Path] | None = None) -> list[Path]:
    """Build ordered list of template search directories.

    Priority: extra_dirs > user config dir > built-in templates.

    Args:
        extra_dirs: Additional directories to search first.

    Returns:
        List of template directories (existing ones only, plus built-in).
    """
    dirs: list[Path] = []

    if extra_dirs:
        dirs.extend(d for d in extra_dirs if d.is_dir())

    # User config directory
    user_dir = Path.home() / ".config" / "transcriber" / "templates"
    if user_dir.is_dir():
        dirs.append(user_dir)

    # Built-in templates always available as fallback
    dirs.append(BUILTIN_TEMPLATE_DIR)

    return dirs


def create_jinja_env(template_dirs: list[Path]) -> Environment:
    """Create a Jinja2 environment from template directories.

    Args:
        template_dirs: Ordered list of directories to search for templates.

    Returns:
        Configured Jinja2 Environment.
    """
    str_dirs = [str(d) for d in template_dirs if d.exists()]

    return Environment(
        loader=FileSystemLoader(str_dirs),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_transcript(
    text: str,
    template_name: str = "default.md",
    extra_template_dirs: list[Path] | None = None,
    metadata: dict | None = None,
) -> str:
    """Render transcript text through a Jinja2 template.

    Args:
        text: The transcript text to format.
        template_name: Template filename (e.g., "blog.md").
        extra_template_dirs: Additional template directories to search.
        metadata: Optional metadata dict passed to the template context.

    Returns:
        Rendered output string.
    """
    template_dirs = get_template_dirs(extra_dirs=extra_template_dirs)
    env = create_jinja_env(template_dirs)

    template = env.get_template(template_name)

    context = {
        "content": text,
        "metadata": metadata or {},
    }

    return template.render(**context)


def list_templates(extra_dirs: list[Path] | None = None) -> list[str]:
    """List available template names.

    Args:
        extra_dirs: Additional template directories to search.

    Returns:
        Sorted list of unique template filenames.
    """
    template_dirs = get_template_dirs(extra_dirs=extra_dirs)
    seen: set[str] = set()
    templates: list[str] = []

    for d in template_dirs:
        if d.is_dir():
            for f in sorted(d.iterdir()):
                if f.is_file() and f.suffix in (".md", ".txt", ".j2") and f.name not in seen:
                    seen.add(f.name)
                    templates.append(f.name)

    return sorted(templates)
