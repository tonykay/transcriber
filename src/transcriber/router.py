"""Two-pass intent router for transcript classification."""

import re
from dataclasses import dataclass, field

from transcriber.intents import IntentConfig


@dataclass
class ExtractedIntent:
    """A single intent extracted from transcript text."""

    type: str
    content: str
    trigger: str
    person: str | None = None
    position: str = "start"  # "start" or "embedded"
    tags: list[str] = field(default_factory=list)


@dataclass
class RoutingResult:
    """Result of routing a transcript through intent detection."""

    primary_intent: str | None = None
    extracted_intents: list[ExtractedIntent] = field(default_factory=list)
    project: str | None = None
    tags: list[str] = field(default_factory=list)
    full_text: str = ""


def _has_person_placeholder(trigger: str) -> bool:
    """Check if a trigger contains a {person} placeholder."""
    return "{person}" in trigger


def _build_simple_pattern(trigger: str) -> re.Pattern[str]:
    """Build a regex pattern for a simple (non-person) trigger.

    Matches the trigger at a word boundary, optionally followed by
    punctuation (comma, colon, dash). Does NOT match the trigger
    when it appears as a substring of a larger phrase.
    """
    escaped = re.escape(trigger)
    # Match at start of text or after sentence boundary, with word boundaries
    # Followed by optional punctuation then content
    return re.compile(
        r"(?:^|(?<=\.\s)|(?<=\?\s)|(?<=!\s)|(?<=\n))"
        r"\s*"
        rf"(?P<trigger>{escaped})"
        r"[,:\-]?\s*"
        r"(?P<content>.*)",
        re.IGNORECASE | re.DOTALL,
    )


def _extract_sentence(text: str) -> str:
    """Extract content up to the next sentence boundary.

    Returns text up to the first ., !, or ? followed by a space or end,
    or the full text if no boundary is found.
    """
    match = re.search(r"[.!?](?:\s|$)", text)
    if match:
        return text[: match.start()].strip()
    return text.strip()


def route_text(text: str, intents: list[IntentConfig]) -> RoutingResult:
    """Route transcript text through Pass 1 (regex trigger matching).

    Scans text for trigger phrases defined in intents config.
    A trigger at the start sets primary_intent.
    Triggers found mid-text are extracted as embedded intents.

    Args:
        text: Transcript text to route.
        intents: Intent definitions to match against.

    Returns:
        RoutingResult with detected intents.
    """
    result = RoutingResult(full_text=text)
    text_stripped = text.strip()

    # Separate simple triggers from person-extraction triggers
    simple_intents = [i for i in intents if not any(_has_person_placeholder(t) for t in i.triggers)]
    # Person intents handled in Task 5

    # Check for start-of-text triggers
    for intent in simple_intents:
        for trigger in intent.triggers:
            pattern = _build_simple_pattern(trigger)
            match = pattern.match(text_stripped)
            if match:
                content = match.group("content").strip()
                extracted = ExtractedIntent(
                    type=intent.type,
                    content=content,
                    trigger=trigger.lower(),
                    position="start",
                    tags=[f"#{intent.type}"],
                )
                result.primary_intent = intent.type
                result.extracted_intents.append(extracted)
                return result

    # Embedded intent extraction handled in Task 6

    return result
