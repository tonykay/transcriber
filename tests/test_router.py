"""Tests for intent router."""

from transcriber.intents import IntentConfig
from transcriber.router import ExtractedIntent, RoutingResult, route_text


def _todo_intent() -> IntentConfig:
    return IntentConfig(
        type="todo", triggers=["todo", "to do", "reminder"],
        output="append", target="todos.md",
    )


def _article_intent() -> IntentConfig:
    return IntentConfig(
        type="article_idea", triggers=["article idea", "blog idea"],
        output="file", target="article-ideas/",
    )


def _note_intent() -> IntentConfig:
    return IntentConfig(
        type="note", triggers=["note", "quick note"],
        output="append", target="notes.md",
    )


def test_route_text_detects_start_trigger():
    """Should detect trigger at start of text and set primary_intent."""
    result = route_text("Todo watch the Nvidia keynote", [_todo_intent()])
    assert result.primary_intent == "todo"
    assert len(result.extracted_intents) == 1
    assert result.extracted_intents[0].content == "watch the Nvidia keynote"
    assert result.extracted_intents[0].position == "start"


def test_route_text_case_insensitive():
    """Trigger matching should be case-insensitive."""
    result = route_text("TODO buy groceries", [_todo_intent()])
    assert result.primary_intent == "todo"


def test_route_text_strips_trigger_from_content():
    """Extracted content should not include the trigger phrase."""
    result = route_text("Reminder call the dentist", [_todo_intent()])
    assert result.extracted_intents[0].content == "call the dentist"
    assert result.extracted_intents[0].trigger == "reminder"


def test_route_text_no_match_returns_empty():
    """Should return no intents when no triggers match."""
    result = route_text("Just a regular transcript about my day.", [_todo_intent()])
    assert result.primary_intent is None
    assert result.extracted_intents == []


def test_route_text_multi_word_trigger():
    """Should match multi-word triggers like 'article idea'."""
    result = route_text("Article idea why voice capture changes everything", [_article_intent()])
    assert result.primary_intent == "article_idea"
    assert result.extracted_intents[0].content == "why voice capture changes everything"


def test_route_text_word_boundary():
    """Should not match 'to do' inside 'want to do something'."""
    result = route_text("I want to do something about this project.", [_todo_intent()])
    assert result.primary_intent is None
    assert result.extracted_intents == []


def test_route_text_trigger_with_punctuation():
    """Should match trigger followed by comma or colon."""
    result = route_text("Todo, watch the Nvidia keynote", [_todo_intent()])
    assert result.primary_intent == "todo"
    assert result.extracted_intents[0].content == "watch the Nvidia keynote"


def test_route_text_preserves_full_text():
    """RoutingResult should preserve the original full text."""
    text = "Todo buy milk"
    result = route_text(text, [_todo_intent()])
    assert result.full_text == text


def test_route_text_intent_tags():
    """Extracted intent should include type as a tag."""
    result = route_text("Todo buy milk", [_todo_intent()])
    assert "#todo" in result.extracted_intents[0].tags
