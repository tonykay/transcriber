# Data Model: Paragraph Reformatter

**Feature**: Paragraph Reformatter Modelfile
**Date**: 2025-10-16
**Status**: Simple stateless transformation - no persistent data model

## Overview

The Paragraph Reformatter is a stateless text transformation tool implemented as an Ollama Modelfile. It does not maintain state, persist data, or use complex data structures. This document describes the conceptual input/output model.

## Conceptual Model

### Input Text

**Type**: String (UTF-8 encoded text)

**Attributes**:
- `content`: The raw, unformatted text to be processed
- `encoding`: UTF-8 (implicit)
- `length`: Variable (up to ~10,000 words recommended)

**Format**: Plain text, potentially from:
- Speech-to-text transcription output (primary use case)
- Manual text entry
- File content

**Characteristics**:
- May have no paragraph breaks (continuous text)
- May have existing paragraph breaks (to be preserved if logical)
- Contains sentences with punctuation
- May include special characters, numbers, URLs, code blocks

**Validation Rules**:
- Must be valid UTF-8 text
- Should contain complete sentences with punctuation
- Maximum practical length: ~10,000 words (model context limit consideration)

### Reformatted Text

**Type**: String (UTF-8 encoded text)

**Attributes**:
- `content`: The reformatted text with paragraph breaks
- `encoding`: UTF-8 (implicit)
- `paragraph_breaks`: Double newline characters (`\n\n`) inserted at logical boundaries

**Format**: Plain text with paragraph structure

**Guarantees**:
- **Content Preservation**: 100% word-for-word match with input (excluding whitespace)
- **Paragraph Structure**: Logical grouping of 3-8 sentences per paragraph on average
- **Formatting Preservation**: Original punctuation, capitalization maintained
- **No Additions**: No new words, corrections, or commentary added
- **No Deletions**: All original words preserved

### Transformation Process

```
┌─────────────────┐
│   Input Text    │
│  (unformatted)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ollama Model   │
│ (transcriber-   │
│   reformat)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reformatted Text│
│ (with ¶ breaks) │
└─────────────────┘
```

**Process Characteristics**:
- **Stateless**: No memory between invocations
- **Deterministic**: Low temperature (0.3) produces consistent results
- **One-way**: No feedback loop or iterative refinement
- **Synchronous**: Blocks until complete
- **Single-threaded**: Processes one text at a time

## Paragraph Detection Logic

### Indicators for Paragraph Breaks

The model uses these signals to determine where to insert paragraph breaks:

1. **Topic Shifts**: New subject introduced
   - Example: "...about the weather. Yesterday's meeting..." → break before "Yesterday's"

2. **Speaker Transitions**: Change in speaker (interviews/dialogues)
   - Example: "...I think so. John replied that..." → break before "John"

3. **Temporal Shifts**: Time-related transitions
   - Example: "...finished the task. Later that day..." → break before "Later"

4. **Logical Conclusions**: Completion of thought followed by new idea
   - Example: "...was resolved. Another issue arose..." → break before "Another"

5. **Lists/Enumerations**: Before and after list structures
   - Example: "...three points: 1) First... 2) Second... 3) Third. After considering..." → breaks before and after list

### Paragraph Characteristics

**Target Profile**:
- Length: 3-8 sentences per paragraph
- Cohesion: Related ideas grouped together
- Flow: Natural reading progression
- Boundaries: Clear topic/time/speaker transitions

## Edge Cases

### Already Formatted Text

**Input**: Text with existing paragraph breaks

**Behavior**: Preserve existing breaks if they align with logical boundaries

**Example**:
```
Input: "Sentence one.\n\nSentence two in new paragraph."
Output: (same) - existing structure preserved
```

### Very Short Text

**Input**: Single sentence or very brief text

**Behavior**: Return unchanged - no artificial paragraph breaks

**Example**:
```
Input: "This is a single sentence."
Output: "This is a single sentence."
```

### Lists and Enumerations

**Input**: Numbered or bulleted lists

**Behavior**: Keep list items together, add breaks before/after list

**Example**:
```
Input: "Here are three points: 1) First point here. 2) Second point here. 3) Third point here. Those were the points."
Output: "Here are three points:

1) First point here. 2) Second point here. 3) Third point here.

Those were the points."
```

### Technical Content

**Input**: Text with code blocks, URLs, technical terms

**Behavior**: Preserve all technical elements unchanged

**Example**:
```
Input: "Visit https://example.com for details. The function does_something() returns True. More info follows."
Output: (same with paragraph break) "Visit https://example.com for details. The function does_something() returns True.

More info follows."
```

## Non-Functional Characteristics

### Performance Model

**Processing Time** (approximate, on Apple Silicon):
- Input: < 100 words → 2-5 seconds
- Input: 500-2000 words → 10-25 seconds
- Input: 5000-10000 words → 25-45 seconds

**Resource Usage**:
- Memory: Handled by Ollama runtime (~2-4 GB for model)
- CPU: Single-threaded, benefits from GPU acceleration
- Disk: No storage (stateless transformation)

### Error Handling

**Model Errors**:
- Ollama runtime handles model loading failures
- Context length exceeded: Model truncates or returns error
- Invalid UTF-8: Ollama pre-processes input

**Content Validation**:
- No pre-validation performed
- Garbage-in, garbage-out principle
- User responsible for providing sensible text input

## Integration Points

### File System Integration

```
Input Location:  ~/Resources/Transcripts/text-unprocessed/
Process:         ollama run transcriber-reformat < input.txt
Output Location: ~/Resources/Transcripts/text-processed/ (optional)
```

### Pipeline Integration

The reformatter can integrate at multiple points:
1. **After Parakeet (Stage 2)**: Format raw transcriptions
2. **Alternative to Transcriber (Stage 3)**: Pure formatting without enhancement
3. **Manual/Standalone**: Process any text file independently

No database, no persistence, no state tracking required.

## Validation Schema

### Content Preservation Validation

```bash
# Word count must match
original_words=$(echo "$input" | wc -w)
output_words=$(echo "$output" | wc -w)
[ "$original_words" -eq "$output_words" ] || echo "ERROR: Word count mismatch"

# Word-for-word diff (sorted)
diff <(echo "$input" | tr -s '[:space:]' '\n' | sort) \
     <(echo "$output" | tr -s '[:space:]' '\n' | sort)
# Empty diff = 100% preservation
```

### Quality Validation

```bash
# Paragraph count
paragraph_count=$(echo "$output" | grep -c '^$')

# Average sentences per paragraph
sentence_count=$(echo "$output" | grep -o '\.' | wc -l)
avg_sentences=$((sentence_count / (paragraph_count + 1)))

# Should be between 3-8 sentences/paragraph
[ "$avg_sentences" -ge 3 ] && [ "$avg_sentences" -le 8 ] && echo "Quality: PASS"
```

## Summary

The Paragraph Reformatter has a trivial data model:
- **Input**: Unformatted text string
- **Output**: Formatted text string with paragraph breaks
- **Transformation**: Stateless, deterministic, content-preserving
- **Storage**: None (ephemeral processing)
- **State**: None (no memory between invocations)

The simplicity is intentional - this is a single-purpose formatting tool, not a data management system.
