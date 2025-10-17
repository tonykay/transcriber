# Quickstart: Paragraph Reformatter Modelfile

**Feature**: Paragraph Reformatter
**Model Name**: `transcriber-reformat`
**Purpose**: Transform unstructured text into well-formatted paragraphs while preserving 100% original content

## Prerequisites

- Ollama installed and running
- Existing `transcriber` project environment
- Access to `Modelfiles/` directory

## Installation

### 1. Create the Model

```bash
# Navigate to Modelfiles directory
cd /Users/tok/Dropbox/PARAL/Projects/transcriber/Modelfiles

# Create the model from Modelfile-reformat
ollama create transcriber-reformat -f Modelfile-reformat
```

Expected output:
```
transferring model data
using existing layer sha256:...
creating new layer sha256:...
writing manifest
success
```

### 2. Verify Installation

```bash
# List available models (should see transcriber-reformat)
ollama list

# Test with simple input
echo "This is sentence one. This is sentence two. Now a new topic. This is sentence three. Another new topic here. Final sentence." | ollama run transcriber-reformat
```

Expected output:
```
This is sentence one. This is sentence two.

Now a new topic. This is sentence three.

Another new topic here. Final sentence.
```

## Basic Usage

### Interactive Mode

```bash
# Start interactive session
ollama run transcriber-reformat

# Paste or type your text, then press Ctrl+D to submit
```

### Pipe from File

```bash
# Process a text file
ollama run transcriber-reformat < input.txt > output.txt
```

### Command Line Input

```bash
# Direct echo
echo "Your unformatted text here..." | ollama run transcriber-reformat

# Using heredoc for multi-line input
ollama run transcriber-reformat <<EOF
This is the first sentence. This is the second sentence.
Now we're talking about something completely different.
This continues the new topic. And this adds more to it.
EOF
```

## Common Use Cases

### 1. Process Raw Transcripts

```bash
# After running Parakeet transcription
cd ~/Resources/Transcripts/text-unprocessed

# Reformat a specific transcript
ollama run transcriber-reformat < raw-transcript.txt > ../text-processed/formatted-transcript.txt
```

### 2. Batch Processing

```bash
# Process all unformatted transcripts
cd ~/Resources/Transcripts/text-unprocessed

for file in *.txt; do
    echo "Processing $file..."
    ollama run transcriber-reformat < "$file" > "../text-processed/formatted-$file"
done
```

### 3. Integration with Transcriber Pipeline

```bash
# After Stage 2 (Parakeet transcription), optionally reformat
cd ~/Resources/Transcripts

# Process specific file
text_file="text-unprocessed/2025-10-16-14:30:00.txt"
formatted_file="text-processed/formatted-$(basename "$text_file")"

ollama run transcriber-reformat < "$text_file" > "$formatted_file"
```

### 4. Preview Before Processing

```bash
# Show original
echo "=== ORIGINAL ==="
cat input.txt

# Show reformatted
echo -e "\n=== REFORMATTED ==="
ollama run transcriber-reformat < input.txt
```

## Validation

### Verify Content Preservation

```bash
# Word-for-word comparison (should show no differences)
original_file="input.txt"
reformatted_file="output.txt"

# Extract and compare all words
diff <(cat "$original_file" | tr -s '[:space:]' '\n' | sort) \
     <(cat "$reformatted_file" | tr -s '[:space:]' '\n' | sort)

# If no output, content is 100% preserved
```

### Check Paragraph Quality

```bash
# Count paragraphs in output
paragraph_count=$(cat output.txt | grep -c '^$')
echo "Paragraph breaks: $paragraph_count"

# Average sentences per paragraph
total_sentences=$(cat output.txt | grep -o '\.' | wc -l)
avg_sentences=$((total_sentences / (paragraph_count + 1)))
echo "Average sentences per paragraph: $avg_sentences"
```

## Performance Testing

```bash
# Time the processing
time ollama run transcriber-reformat < large-transcript.txt > /dev/null

# Example output:
# real    0m18.234s
# user    0m0.123s
# sys     0m0.045s
```

Expected performance:
- Short text (< 100 words): 2-5 seconds
- Typical transcript (500-2000 words): 10-25 seconds
- Long transcript (5000+ words): 25-45 seconds

## Troubleshooting

### Model Not Found

```bash
# Error: model 'transcriber-reformat' not found

# Solution: Create the model
ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat
```

### Output Contains Extra Text

If the model adds preamble like "Here is the reformatted text:", the SYSTEM prompt may need adjustment. The current configuration should prevent this, but if it occurs:

```bash
# Remove the model and recreate
ollama rm transcriber-reformat
ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat
```

### Content Not Preserved

```bash
# Compare original and output
diff input.txt output.txt

# If differences are substantial (not just whitespace), check:
# 1. Model created from correct Modelfile
# 2. Base model (llama3.2) is available
# 3. No intermediate processing modified content
```

### Slow Performance

```bash
# Check Ollama is using GPU acceleration (on Apple Silicon)
ollama ps

# Ensure no other heavy processes are running
top -o cpu

# Consider using mistral for faster inference
# Edit Modelfile-reformat: FROM mistral:latest
ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat
```

## Advanced Usage

### Custom Temperature

If you want more or less variation in paragraph breaks:

```bash
# Edit Modelfile-reformat
# Change: PARAMETER temperature 0.3
# To:     PARAMETER temperature 0.5  (more variation)
# Or:     PARAMETER temperature 0.1  (more deterministic)

# Recreate model
ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat
```

### Process Only New Files

```bash
# Process only files not yet reformatted
cd ~/Resources/Transcripts

for file in text-unprocessed/*.txt; do
    basename=$(basename "$file")
    output_file="text-processed/formatted-$basename"

    if [ ! -f "$output_file" ]; then
        echo "Reformatting new file: $basename"
        ollama run transcriber-reformat < "$file" > "$output_file"
    fi
done
```

### Compare with Transcriber Model

```bash
# Compare paragraph reformatter vs full transcriber enhancement
input="text-unprocessed/sample.txt"

echo "=== Paragraph Reformatter ==="
ollama run transcriber-reformat < "$input"

echo -e "\n=== Full Transcriber Enhancement ==="
ollama run transcriber < "$input"
```

## Model Management

### Update the Model

```bash
# After modifying Modelfile-reformat
ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat

# Old version is automatically replaced
```

### Remove the Model

```bash
# If no longer needed
ollama rm transcriber-reformat
```

### Check Model Info

```bash
# View model details
ollama show transcriber-reformat

# View model configuration
ollama show transcriber-reformat --modelfile
```

## Next Steps

- Test with your actual transcripts from DJI Mic recordings
- Integrate into `transcriber.sh` if desired (optional enhancement)
- Compare output quality vs full transcriber model
- Adjust temperature parameter if needed for your use case

## Support

For issues specific to:
- Ollama functionality: https://github.com/ollama/ollama/issues
- This reformatter: Review the [spec.md](./spec.md) and [research.md](./research.md)
- Integration with transcriber pipeline: See main project README.md
