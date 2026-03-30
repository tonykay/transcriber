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


_PERSON_STOP_WORDS = ("about", "regarding", "that")


def _build_person_pattern(trigger: str) -> re.Pattern[str]:
    """Build a regex pattern for a trigger with {person} placeholder.

    The {person} group captures one or more capitalized words (a name)
    up to a stop word like 'about', 'regarding', 'that'.
    """
    parts = trigger.split("{person}")
    before = re.escape(parts[0].strip())
    after = parts[1].strip() if len(parts) > 1 else ""
    after_escaped = re.escape(after).strip()

    return re.compile(
        r"(?:^|(?<=\.\s)|(?<=\?\s)|(?<=!\s)|(?<=\n))"
        r"\s*"
        rf"(?P<trigger_before>{before})\s+"
        r"(?P<person>[\w\s]+?)\s+"
        rf"{after_escaped}\s*"
        r"(?P<content>.*)",
        re.IGNORECASE | re.DOTALL,
    )


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


def _build_embedded_person_pattern(trigger: str) -> re.Pattern[str]:
    """Build a regex for a person trigger that can appear anywhere in text."""
    parts = trigger.split("{person}")
    before = re.escape(parts[0].strip())
    after = parts[1].strip() if len(parts) > 1 else ""
    after_escaped = re.escape(after).strip()

    return re.compile(
        rf"(?:^|.*?\b)"
        rf"(?P<trigger_before>{before})\s+"
        r"(?P<person>[\w\s]+?)\s+"
        rf"{after_escaped}\s*"
        r"(?P<content>.*)",
        re.IGNORECASE | re.DOTALL,
    )


def _build_embedded_simple_pattern(trigger: str) -> re.Pattern[str]:
    """Build a regex for a simple trigger that can appear anywhere in text.

    Uses a word boundary before the trigger to avoid matching triggers
    that appear as substrings of larger phrases (e.g., 'to do' in 'want to do').
    The trigger must either start the sentence or follow a sentence boundary
    marker (period/comma + space, or start after 'and'/'also'/etc.).
    """
    escaped = re.escape(trigger)
    return re.compile(
        r"(?:^|.*?(?:^|[.!?,;]\s+|(?:and|also|oh)\s+))"
        rf"(?P<trigger>{escaped})"
        r"[,:\-]?\s*"
        r"(?P<content>.*)",
        re.IGNORECASE | re.DOTALL,
    )


def _extract_embedded_intents(
    text: str, intents: list[IntentConfig]
) -> list[ExtractedIntent]:
    """Scan text for trigger phrases at sentence boundaries.

    Looks for triggers after sentence-ending punctuation (. ! ?)
    and extracts content up to the next sentence boundary.
    """
    extracted: list[ExtractedIntent] = []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if not sentence_stripped:
            continue

        # Check person triggers first (more specific)
        person_intents = [i for i in intents if any(_has_person_placeholder(t) for t in i.triggers)]
        matched = False

        for intent in person_intents:
            if matched:
                break
            for trigger in intent.triggers:
                if not _has_person_placeholder(trigger):
                    continue
                pattern = _build_embedded_person_pattern(trigger)
                match = pattern.match(sentence_stripped)
                if match:
                    person = match.group("person").strip()
                    content = _extract_sentence(match.group("content").strip())
                    tags = [f"#{intent.type}", f"#{person.lower().replace(' ', '_')}"]
                    extracted.append(ExtractedIntent(
                        type=intent.type,
                        content=content,
                        trigger=trigger.lower(),
                        person=person,
                        position="embedded",
                        tags=tags,
                    ))
                    matched = True
                    break

        if matched:
            continue

        # Check simple triggers
        simple_intents = [i for i in intents if not any(_has_person_placeholder(t) for t in i.triggers)]
        for intent in simple_intents:
            if matched:
                break
            for trigger in intent.triggers:
                pattern = _build_embedded_simple_pattern(trigger)
                match = pattern.match(sentence_stripped)
                if match:
                    content = _extract_sentence(match.group("content").strip())
                    extracted.append(ExtractedIntent(
                        type=intent.type,
                        content=content,
                        trigger=trigger.lower(),
                        position="embedded",
                        tags=[f"#{intent.type}"],
                    ))
                    matched = True
                    break

    return extracted


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
    person_intents = [i for i in intents if any(_has_person_placeholder(t) for t in i.triggers)]

    # Check person-extraction triggers first (more specific)
    for intent in person_intents:
        for trigger in intent.triggers:
            if not _has_person_placeholder(trigger):
                continue
            pattern = _build_person_pattern(trigger)
            match = pattern.match(text_stripped)
            if match:
                person = match.group("person").strip()
                content = match.group("content").strip()
                tags = [f"#{intent.type}", f"#{person.lower().replace(' ', '_')}"]
                extracted = ExtractedIntent(
                    type=intent.type,
                    content=content,
                    trigger=trigger.lower(),
                    person=person,
                    position="start",
                    tags=tags,
                )
                result.primary_intent = intent.type
                result.extracted_intents.append(extracted)
                break
        if result.primary_intent:
            break

    # Check for start-of-text triggers (only if no person trigger matched)
    if not result.primary_intent:
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
                    break
            if result.primary_intent:
                break

    # Scan for embedded intents in remaining text
    if result.primary_intent:
        sentences = re.split(r"(?<=[.!?])\s+", text_stripped)
        if len(sentences) > 1:
            remaining_text = " ".join(sentences[1:])
            embedded = _extract_embedded_intents(remaining_text, intents)
            result.extracted_intents.extend(embedded)
    else:
        # No start trigger — scan entire text for embedded intents
        embedded = _extract_embedded_intents(text_stripped, intents)
        result.extracted_intents.extend(embedded)

    return result
