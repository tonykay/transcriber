#!/usr/bin/env bash
#
# Paragraph Quality Validation Script
# Analyzes paragraph structure and sentence distribution
#
# Usage: ./check-quality.sh <reformatted-file>
#
# Exit codes:
#   0 - Quality acceptable (3-8 sentences per paragraph average)
#   1 - Quality issues (over/under segmentation)
#   2 - Usage error

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <reformatted-file>" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  $0 test-data/output-continuous.txt" >&2
    exit 2
fi

REFORMATTED="$1"

# Check file exists
if [ ! -f "$REFORMATTED" ]; then
    echo "Error: Reformatted file not found: $REFORMATTED" >&2
    exit 2
fi

echo "Analyzing paragraph quality..."
echo "File: $REFORMATTED"
echo ""

# Count paragraphs (separated by blank lines)
# Add 1 because paragraph count = blank line count + 1
BLANK_LINES=$(grep -c '^$' "$REFORMATTED" || echo "0")
PARAGRAPH_COUNT=$((BLANK_LINES + 1))

# Count sentences (periods followed by space or end of line)
# This is a simplified approach that works for most transcripts
SENTENCE_COUNT=$(grep -o '\.' "$REFORMATTED" | wc -l | tr -d ' ')

# Handle edge case of no paragraphs
if [ "$PARAGRAPH_COUNT" -eq 0 ]; then
    echo "⚠️  WARNING: No paragraphs detected (file may be empty)"
    exit 1
fi

# Calculate average sentences per paragraph
AVG_SENTENCES=$((SENTENCE_COUNT / PARAGRAPH_COUNT))

echo "Paragraph Statistics:"
echo "  Total paragraphs: $PARAGRAPH_COUNT"
echo "  Total sentences:  $SENTENCE_COUNT"
echo "  Average sentences/paragraph: $AVG_SENTENCES"
echo ""

# Quality assessment (target: 3-8 sentences per paragraph)
if [ "$AVG_SENTENCES" -ge 3 ] && [ "$AVG_SENTENCES" -le 8 ]; then
    echo "✅ PASS: Paragraph quality acceptable ($AVG_SENTENCES sentences/paragraph)"
    echo ""
    echo "The reformatted text has good paragraph structure."
    exit 0
elif [ "$AVG_SENTENCES" -lt 3 ]; then
    echo "⚠️  WARNING: Possible over-segmentation ($AVG_SENTENCES sentences/paragraph)"
    echo ""
    echo "Paragraphs may be too short. Consider:"
    echo "  - Increasing temperature (current: 0.3) to 0.4-0.5"
    echo "  - Reviewing SYSTEM prompt for overly aggressive break indicators"
    exit 1
elif [ "$AVG_SENTENCES" -gt 8 ]; then
    echo "⚠️  WARNING: Possible under-segmentation ($AVG_SENTENCES sentences/paragraph)"
    echo ""
    echo "Paragraphs may be too long. Consider:"
    echo "  - Decreasing temperature (current: 0.3) to 0.2"
    echo "  - Enhancing SYSTEM prompt with more break indicators"
    exit 1
else
    echo "✅ PASS: Paragraph quality acceptable"
    exit 0
fi
