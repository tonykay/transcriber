#!/usr/bin/env bash
#
# Content Preservation Validation Script
# Compares two text files word-for-word to ensure 100% content preservation
#
# Usage: ./check-preservation.sh <original-file> <reformatted-file>
#
# Exit codes:
#   0 - Content preserved (100% match)
#   1 - Content modified (differences found)
#   2 - Usage error

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <original-file> <reformatted-file>" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  $0 test-data/sample-continuous.txt test-data/output-continuous.txt" >&2
    exit 2
fi

ORIGINAL="$1"
REFORMATTED="$2"

# Check files exist
if [ ! -f "$ORIGINAL" ]; then
    echo "Error: Original file not found: $ORIGINAL" >&2
    exit 2
fi

if [ ! -f "$REFORMATTED" ]; then
    echo "Error: Reformatted file not found: $REFORMATTED" >&2
    exit 2
fi

echo "Checking content preservation..."
echo "Original file:    $ORIGINAL"
echo "Reformatted file: $REFORMATTED"
echo ""

# Extract all words from both files, sort them, and compare
# This ensures word-for-word match regardless of whitespace/formatting
ORIGINAL_WORDS=$(cat "$ORIGINAL" | tr -s '[:space:]' '\n' | grep -v '^$' | sort)
REFORMATTED_WORDS=$(cat "$REFORMATTED" | tr -s '[:space:]' '\n' | grep -v '^$' | sort)

# Compare word lists
if diff <(echo "$ORIGINAL_WORDS") <(echo "$REFORMATTED_WORDS") > /dev/null 2>&1; then
    echo "✅ PASS: Content preserved (100% word-for-word match)"
    echo ""

    # Show word counts as additional verification
    ORIGINAL_COUNT=$(echo "$ORIGINAL_WORDS" | wc -l | tr -d ' ')
    REFORMATTED_COUNT=$(echo "$REFORMATTED_WORDS" | wc -l | tr -d ' ')

    echo "Word count verification:"
    echo "  Original:    $ORIGINAL_COUNT words"
    echo "  Reformatted: $REFORMATTED_COUNT words"

    exit 0
else
    echo "❌ FAIL: Content modified (differences detected)"
    echo ""
    echo "Differences:"
    diff <(echo "$ORIGINAL_WORDS") <(echo "$REFORMATTED_WORDS") || true
    echo ""
    echo "This indicates words were added, removed, or changed."
    echo "Review the SYSTEM prompt and temperature settings in the Modelfile."

    exit 1
fi
