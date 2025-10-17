#!/usr/bin/env bash
#
# Transcript Reformatter Helper Script
#
# This script helps reformat existing transcript files using the transcriber-reformat model.
# It can process single files or batch process all files in a directory.
#
# Usage:
#   ./reformat-transcript.sh <input-file> [output-file]
#   ./reformat-transcript.sh --batch <input-directory> [output-directory]
#
# Examples:
#   # Reformat a single file
#   ./reformat-transcript.sh input.txt output.txt
#
#   # Reformat to stdout
#   ./reformat-transcript.sh input.txt
#
#   # Batch process a directory
#   ./reformat-transcript.sh --batch ~/Resources/Transcripts/text-unprocessed ~/Resources/Transcripts/reformatted
#

set -e

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if ollama and transcriber-reformat model are available
check_prerequisites() {
    if ! command -v ollama &> /dev/null; then
        error "ollama command not found. Please install Ollama from https://ollama.com"
    fi

    if ! ollama list | grep -q "transcriber-reformat"; then
        error "transcriber-reformat model not found. Please run: ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat"
    fi
}

# Reformat a single file
reformat_file() {
    local input_file="$1"
    local output_file="$2"

    if [ ! -f "$input_file" ]; then
        error "Input file not found: $input_file"
    fi

    info "Reformatting: $input_file"

    if [ -n "$output_file" ]; then
        ollama run transcriber-reformat < "$input_file" > "$output_file"
        success "Output written to: $output_file"
    else
        ollama run transcriber-reformat < "$input_file"
    fi
}

# Batch reformat files in a directory
batch_reformat() {
    local input_dir="$1"
    local output_dir="$2"

    if [ ! -d "$input_dir" ]; then
        error "Input directory not found: $input_dir"
    fi

    # Create output directory if specified
    if [ -n "$output_dir" ]; then
        mkdir -p "$output_dir"
        info "Output directory: $output_dir"
    fi

    # Count text files
    local file_count=$(find "$input_dir" -maxdepth 1 -name "*.txt" | wc -l | tr -d ' ')

    if [ "$file_count" -eq 0 ]; then
        error "No .txt files found in $input_dir"
    fi

    info "Found $file_count .txt files to process"
    echo ""

    # Process each file
    local processed=0
    for input_file in "$input_dir"/*.txt; do
        [ -e "$input_file" ] || continue

        local filename=$(basename "$input_file")
        local output_file

        if [ -n "$output_dir" ]; then
            output_file="$output_dir/$filename"
        else
            # If no output directory, add suffix to original directory
            output_file="${input_file%.txt}-reformatted.txt"
        fi

        reformat_file "$input_file" "$output_file"
        ((processed++))
        echo ""
    done

    success "Batch processing complete: $processed files reformatted"
}

# Show usage information
usage() {
    cat << EOF
Transcript Reformatter Helper Script

USAGE:
    Single file:
        $0 <input-file> [output-file]

    Batch processing:
        $0 --batch <input-directory> [output-directory]

EXAMPLES:
    # Reformat single file to new file
    $0 input.txt output.txt

    # Reformat to stdout
    $0 input.txt

    # Batch process directory (adds -reformatted suffix)
    $0 --batch ~/Resources/Transcripts/text-unprocessed

    # Batch process to separate output directory
    $0 --batch ~/Resources/Transcripts/text-unprocessed ~/Resources/Transcripts/reformatted

DESCRIPTION:
    This script uses the transcriber-reformat Ollama model to add paragraph breaks
    to continuous text while preserving 100% of the original content.

PREREQUISITES:
    - Ollama installed (https://ollama.com)
    - transcriber-reformat model created:
      ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat

EOF
}

# Main script logic
main() {
    # Check prerequisites
    check_prerequisites

    # Handle command line arguments
    if [ $# -eq 0 ]; then
        usage
        exit 0
    fi

    if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        usage
        exit 0
    fi

    if [ "$1" == "--batch" ]; then
        shift
        batch_reformat "$@"
    else
        reformat_file "$@"
    fi
}

main "$@"
