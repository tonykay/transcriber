"""Tests for intent router."""

import json
from unittest.mock import MagicMock, patch

from transcriber.intents import IntentConfig
from transcriber.router import ExtractedIntent, RoutingResult, route_text, route_text_with_fallback


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


def _person_intent() -> IntentConfig:
    return IntentConfig(
        type="todo",
        triggers=["speak to {person} about", "ask {person} about", "talk to {person} about", "tell {person} about"],
        output="append",
        target="todos.md",
        extract={"person": "frontmatter"},
    )


def test_route_text_person_extraction():
    """Should extract person name from 'speak to {person} about' trigger."""
    result = route_text("Speak to John about attending KubeCon", [_person_intent()])
    assert result.primary_intent == "todo"
    assert result.extracted_intents[0].person == "John"
    assert result.extracted_intents[0].content == "attending KubeCon"
    assert "#john" in result.extracted_intents[0].tags


def test_route_text_person_ask_variant():
    """Should handle 'ask {person} about' variant."""
    result = route_text("Ask Sarah about the deployment timeline", [_person_intent()])
    assert result.extracted_intents[0].person == "Sarah"
    assert result.extracted_intents[0].content == "the deployment timeline"


def test_route_text_person_case_insensitive():
    """Person extraction trigger should be case-insensitive."""
    result = route_text("TELL james about the new API", [_person_intent()])
    assert result.extracted_intents[0].person == "james"


def test_route_text_person_multi_word_name():
    """Should extract multi-word names before stop word."""
    result = route_text("Talk to Mary Jane about the project", [_person_intent()])
    assert result.extracted_intents[0].person == "Mary Jane"
    assert result.extracted_intents[0].content == "the project"


def test_route_text_embedded_intent():
    """Should extract embedded trigger from mid-text."""
    text = (
        "We should really show the GitOps workflow. "
        "Todo, ask James about the cluster quota limits. "
        "Anyway back to the demo flow."
    )
    result = route_text(text, [_todo_intent(), _person_intent()])
    assert result.primary_intent is None  # no start trigger
    assert len(result.extracted_intents) == 1
    intent = result.extracted_intents[0]
    assert intent.type == "todo"
    assert intent.position == "embedded"
    assert intent.person == "James"


def test_route_text_multiple_embedded():
    """Should extract multiple embedded intents."""
    text = (
        "Working on the summit lab. "
        "Todo buy new cables for the demo. "
        "Also, reminder to book flights."
    )
    result = route_text(text, [_todo_intent()])
    assert len(result.extracted_intents) == 2
    assert all(i.position == "embedded" for i in result.extracted_intents)


def test_route_text_start_plus_embedded():
    """Start trigger and embedded trigger should both fire."""
    text = (
        "Article idea why voice capture changes everything. "
        "Oh and todo, buy a new microphone."
    )
    result = route_text(text, [_todo_intent(), _article_intent()])
    assert result.primary_intent == "article_idea"
    assert len(result.extracted_intents) == 2
    types = [i.type for i in result.extracted_intents]
    assert "article_idea" in types
    assert "todo" in types


def test_route_text_embedded_sentence_boundary():
    """Embedded extraction should stop at sentence boundary."""
    text = (
        "General discussion here. "
        "Reminder check the CI pipeline status. "
        "Back to regular discussion."
    )
    result = route_text(text, [_todo_intent()])
    assert result.extracted_intents[0].content == "check the CI pipeline status"


def test_route_text_with_llm_fallback():
    """Should use LLM fallback when no regex triggers match."""
    llm_response = json.dumps({
        "intents": [{"type": "todo", "content": "review the PR", "position": "embedded"}],
        "suggested_tags": ["#code_review"],
    })

    mock_provider = MagicMock()
    mock_provider.is_available.return_value = True
    mock_result = MagicMock()
    mock_result.stdout = llm_response
    mock_provider.classify.return_value = mock_result

    result = route_text_with_fallback(
        text="I should probably review that pull request soon.",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert len(result.extracted_intents) == 1
    assert result.extracted_intents[0].type == "todo"
    assert result.extracted_intents[0].content == "review the PR"


def test_route_text_with_llm_fallback_no_intent():
    """LLM fallback returning 'none' should produce empty result."""
    llm_response = json.dumps({
        "intents": [{"type": "none", "content": "", "position": "start"}],
        "suggested_tags": ["#general"],
    })

    mock_provider = MagicMock()
    mock_provider.is_available.return_value = True
    mock_result = MagicMock()
    mock_result.stdout = llm_response
    mock_provider.classify.return_value = mock_result

    result = route_text_with_fallback(
        text="Just chatting about the weather today.",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert result.primary_intent is None
    assert result.extracted_intents == []
    assert "#general" in result.tags


def test_route_text_with_llm_fallback_skipped_when_regex_matches():
    """LLM fallback should NOT fire when regex already matched."""
    mock_provider = MagicMock()

    result = route_text_with_fallback(
        text="Todo buy groceries",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert result.primary_intent == "todo"
    mock_provider.classify.assert_not_called()


def test_route_text_with_fallback_unavailable_llm():
    """Should return regex-only result when LLM is unavailable."""
    mock_provider = MagicMock()
    mock_provider.is_available.return_value = False

    result = route_text_with_fallback(
        text="Some text with no triggers.",
        intents=[_todo_intent()],
        llm_provider=mock_provider,
    )
    assert result.primary_intent is None
    assert result.extracted_intents == []
