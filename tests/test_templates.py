"""Tests for Jinja2 template rendering."""

from pathlib import Path

from transcriber.templates import (
    BUILTIN_TEMPLATE_DIR,
    get_template_dirs,
    list_templates,
    render_transcript,
)


def test_builtin_template_dir_exists():
    """Built-in template directory should exist."""
    assert BUILTIN_TEMPLATE_DIR.is_dir()


def test_builtin_templates_include_defaults():
    """Built-in templates should include the standard set."""
    templates = list_templates()
    assert "default.md" in templates
    assert "blog.md" in templates
    assert "trip-report.md" in templates
    assert "summary.md" in templates


def test_get_template_dirs_includes_builtin():
    """Template dirs should always include built-in as fallback."""
    dirs = get_template_dirs()
    assert BUILTIN_TEMPLATE_DIR in dirs


def test_get_template_dirs_with_extra(tmp_path: Path):
    """Extra dirs should appear before built-in."""
    custom = tmp_path / "custom"
    custom.mkdir()
    dirs = get_template_dirs(extra_dirs=[custom])
    assert dirs[0] == custom
    assert dirs[-1] == BUILTIN_TEMPLATE_DIR


def test_render_transcript_default():
    """Should render through default template."""
    result = render_transcript("Hello world.")
    assert "Hello world." in result
    assert "Transcript" in result


def test_render_transcript_with_metadata():
    """Should pass metadata to template context."""
    result = render_transcript(
        "Some content.",
        template_name="default.md",
        metadata={"source_file": "test.wav", "date": "2025-07-02"},
    )
    assert "test.wav" in result
    assert "2025-07-02" in result


def test_render_transcript_blog_template():
    """Blog template should render with frontmatter."""
    result = render_transcript(
        "Blog content here.",
        template_name="blog.md",
        metadata={"title": "My Post", "date": "2025-07-02"},
    )
    assert "My Post" in result
    assert "Blog content here." in result


def test_render_transcript_custom_template(tmp_path: Path):
    """Should find templates in custom directories."""
    custom_dir = tmp_path / "templates"
    custom_dir.mkdir()
    (custom_dir / "custom.md").write_text("CUSTOM: {{ content }}")

    result = render_transcript(
        "test text",
        template_name="custom.md",
        extra_template_dirs=[custom_dir],
    )
    assert result == "CUSTOM: test text"


def test_list_templates_includes_custom(tmp_path: Path):
    """Custom templates should appear in listing."""
    custom_dir = tmp_path / "templates"
    custom_dir.mkdir()
    (custom_dir / "my-template.md").write_text("{{ content }}")

    templates = list_templates(extra_dirs=[custom_dir])
    assert "my-template.md" in templates
