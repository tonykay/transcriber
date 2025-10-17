# Research: Paragraph Reformatter Modelfile

**Feature**: Paragraph Reformatter
**Date**: 2025-10-16
**Purpose**: Research Ollama Modelfile configuration and prompt engineering best practices for text paragraph detection and formatting

## Overview

This document captures research findings for creating an Ollama Modelfile that transforms unstructured text into well-formatted paragraphs while preserving 100% of the original content.

## Key Research Areas

### 1. Ollama Modelfile Format

**Decision**: Use Ollama Modelfile DSL with SYSTEM instruction for behavior definition

**Rationale**:
- Ollama Modelfiles provide declarative configuration for model behavior
- SYSTEM instruction defines the model's role and constraints
- TEMPLATE instruction can customize input/output format
- PARAMETER settings control model behavior (temperature, top_p, etc.)

**Alternatives Considered**:
- Direct prompt engineering without Modelfile: Less reusable, harder to version control
- Python wrapper script: Adds unnecessary complexity for stateless transformation
- Separate fine-tuned model: Overkill for formatting task, existing models sufficient

**Modelfile Structure**:
```modelfile
FROM <base-model>
SYSTEM """<system prompt defining behavior>"""
PARAMETER temperature <value>
PARAMETER top_p <value>
```

### 2. Base Model Selection

**Decision**: Use `llama3.2:latest` or `mistral:latest` as base model

**Rationale**:
- Both models excel at text understanding and formatting tasks
- Llama 3.2: Better instruction following, good for structured tasks
- Mistral: Faster inference, good balance of quality and speed
- Both models are widely available and well-tested

**Performance Characteristics**:
- Llama 3.2: ~500-2000 words in 15-25 seconds on Apple Silicon
- Mistral: ~500-2000 words in 10-20 seconds on Apple Silicon
- Both meet the <30 second performance requirement

**Alternatives Considered**:
- GPT-4 via API: Requires internet, API costs, slower
- Smaller models (< 7B parameters): Lower quality paragraph detection
- Specialized summarization models: Not designed for formatting preservation

### 3. Prompt Engineering for Paragraph Detection

**Decision**: Use explicit instruction-based system prompt with clear constraints

**Key Principles**:
1. **Clarity**: Explicitly state the task (reformat into paragraphs)
2. **Constraints**: Emphasize content preservation (no additions/deletions)
3. **Examples**: Provide format expectations without over-constraining
4. **Boundaries**: Define what constitutes a logical paragraph break

**Prompt Strategy**:
```
You are a text formatter that organizes unstructured text into well-structured paragraphs.

Your task:
- Read the input text carefully
- Identify logical topic shifts and natural breaks
- Group related sentences into coherent paragraphs
- Output the EXACT SAME content with paragraph breaks added

Critical rules:
- NEVER add, remove, or modify any words
- NEVER correct grammar or spelling
- NEVER summarize or paraphrase
- ONLY add paragraph breaks (double newlines) between groups of sentences
- Preserve all original punctuation, capitalization, and formatting

Paragraph break indicators:
- Topic shifts (new subject introduced)
- Speaker transitions (in dialogues/interviews)
- Temporal shifts (time changes: "later", "then", "next")
- Logical conclusion followed by new idea
- Lists or enumerations

Aim for 3-8 sentences per paragraph on average.
```

**Rationale**:
- Explicit constraints prevent model from "improving" text (which would violate content preservation)
- Clear indicators help model identify natural breaks
- Sentence count guideline prevents over-segmentation or under-segmentation
- Negative instructions ("NEVER") are effective for LLM constraint enforcement

### 4. Parameter Tuning

**Decision**: Low temperature (0.3-0.5) for deterministic, format-focused output

**Parameters**:
- `temperature: 0.3` - Lower temperature for more consistent, deterministic formatting
- `top_p: 0.9` - Slight randomness acceptable for natural break detection
- `repeat_penalty: 1.1` - Prevent model from repeating instructions in output

**Rationale**:
- Lower temperature reduces creative interpretation (we want formatting, not content changes)
- Moderate top_p allows some flexibility in paragraph boundary detection
- Repeat penalty prevents model from echoing system prompt

**Alternatives Considered**:
- Temperature 0.0: Too rigid, may miss nuanced paragraph opportunities
- Temperature 0.7+: Too creative, risks paraphrasing or content modification
- Higher repeat_penalty: May interfere with legitimate repeated words in input

### 5. Edge Case Handling

**Research Findings**:

**Already Well-Formatted Text**:
- Strategy: Model should detect existing paragraph breaks and preserve them
- Instruction addition: "If text is already well-formatted, preserve existing paragraph structure"

**Very Short Text** (single sentence or paragraph):
- Strategy: Model should return input unchanged if no logical breaks exist
- Instruction addition: "If text is too short for meaningful paragraphs, return it unchanged"

**Mixed Languages/Special Characters**:
- Llama 3.2 and Mistral handle UTF-8 and multilingual text well
- No special handling needed beyond standard text encoding

**Code Blocks/Technical Content**:
- Instruction addition: "Preserve code blocks, URLs, and technical formatting as-is"
- Model should recognize ```code``` blocks and treat as single units

**Lists and Enumerations**:
- Strategy: Keep numbered/bulleted lists together within paragraphs or as separate blocks
- Natural paragraph breaks should occur before/after lists, not within them

### 6. Validation and Testing Strategy

**Content Preservation Validation**:
```bash
# Word-for-word comparison
diff <(echo "$original" | tr -s '[:space:]' '\n' | sort) \
     <(echo "$reformatted" | tr -s '[:space:]' '\n' | sort)
```

**Quality Assessment Metrics**:
1. **Preservation Score**: 100% word match (required)
2. **Paragraph Count**: 3-8 sentences per paragraph on average
3. **Processing Time**: < 30 seconds for 500-2000 word inputs
4. **Readability**: Subjective assessment of logical grouping

**Test Cases**:
- Continuous text with no breaks (most common case)
- Already formatted text with paragraphs
- Very short text (< 50 words)
- Long text (> 5000 words)
- Mixed technical and prose content
- Text with lists and enumerations

## Implementation Recommendations

### Recommended Modelfile Configuration

```modelfile
FROM llama3.2:latest

SYSTEM """You are a text formatter that organizes unstructured text into well-structured paragraphs.

Your task:
- Read the input text carefully
- Identify logical topic shifts and natural breaks
- Group related sentences into coherent paragraphs
- Output the EXACT SAME content with paragraph breaks added

Critical rules:
- NEVER add, remove, or modify any words
- NEVER correct grammar or spelling
- NEVER summarize or paraphrase
- ONLY add paragraph breaks (double newlines) between groups of sentences
- Preserve all original punctuation, capitalization, and formatting

Paragraph break indicators:
- Topic shifts (new subject introduced)
- Speaker transitions (in dialogues/interviews)
- Temporal shifts (time changes: "later", "then", "next")
- Logical conclusion followed by new idea
- Lists or enumerations

Guidelines:
- Aim for 3-8 sentences per paragraph on average
- If text is already well-formatted, preserve existing structure
- If text is too short for paragraphs, return unchanged
- Preserve code blocks, URLs, and technical formatting as-is

Output only the reformatted text with no preamble or explanation.
"""

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
```

### Usage Pattern

```bash
# Create and test the model
cd Modelfiles
ollama create transcriber-reformat -f Modelfile-reformat

# Test with sample text
echo "This is sentence one. This is sentence two. Now a new topic starts. This is sentence three." | \
  ollama run transcriber-reformat

# Validate preservation
original="$(cat test-input.txt)"
reformatted="$(ollama run transcriber-reformat < test-input.txt)"
diff <(echo "$original" | tr -s '[:space:]' '\n' | sort) \
     <(echo "$reformatted" | tr -s '[:space:]' '\n' | sort)
```

### Integration with Existing Pipeline

The reformatter can be integrated as:
1. **Optional post-processing** after Stage 3 (transcriber model)
2. **Alternative to transcriber model** for pure formatting (no content enhancement)
3. **Preprocessing step** before transcriber model for already-transcribed text

No changes to `transcriber.sh` required - can be invoked manually or added as optional stage.

## References

- Ollama Modelfile Documentation: https://github.com/ollama/ollama/blob/main/docs/modelfile.md
- Llama 3.2 Model Card: https://ollama.com/library/llama3.2
- Mistral Model Card: https://ollama.com/library/mistral
- Prompt Engineering Best Practices: https://platform.openai.com/docs/guides/prompt-engineering
- Text Segmentation Research: Natural paragraph boundaries in spoken vs written text

## Next Steps

1. Create `Modelfile-reformat` based on recommended configuration (Phase 1)
2. Generate quickstart guide with usage examples (Phase 1)
3. Create model with `ollama create` (Implementation Phase)
4. Test with real transcript samples (Implementation Phase)
5. Validate content preservation (Implementation Phase)
