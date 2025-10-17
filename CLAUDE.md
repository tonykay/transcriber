# CLAUDE.md - Development Context

## Project Overview
DJI Transcriber - A complete pipeline for processing DJI audio recordings into formatted transcripts using automated speech recognition and AI enhancement.

## Architecture
- **Language**: Bash shell script
- **Main Script**: `transcriber.sh` (executable)
- **Dependencies**:
  - Parakeet MLX (speech-to-text)
  - Ollama with custom `transcriber` model (text enhancement)
  - Ollama `transcriber-reformat` model (optional paragraph formatting)

## Key Functions
- `process_dji_audio()` - Import & rename DJI audio files
- `transcribe_audio_files()` - Convert audio to text using Parakeet MLX
- `process_transcripts()` - Enhance transcripts using Ollama AI

## Directory Structure
```
~/Resources/Transcripts/
├── audio-unprocessed/     # Raw audio from DJI device
├── audio-processed/       # Transcribed audio files
├── text-unprocessed/      # Raw transcription text
├── text-processed/        # Ollama-processed text
└── transcripts/           # Final enhanced markdown
```

## File Naming Convention
- Input: `DJI_01_20250702_175446.WAV`
- Output: `2025-07-02-17:54:46.WAV`
- Final: `transcript-2025-07-02-17:54:46.md`

## Development Commands
```bash
# Test the script
./transcriber.sh

# Source for individual function testing
source transcriber.sh

# Check syntax
bash -n transcriber.sh
```

## Current Status
- ✅ Complete working pipeline
- ✅ Full documentation (README.md, spec.md)
- ✅ Custom Ollama model configuration
- ✅ Error handling and batch processing
- ✅ Clean git repository
- ✅ **Complete**: Paragraph Reformatter Modelfile (feature: 001-paragraph-reformatter)

## Additional Tools

### Paragraph Reformatter (`transcriber-reformat` model)
Optional tool for formatting raw text into structured paragraphs with 100% content preservation.

- **Location**: `Modelfiles/Modelfile-reformat`
- **Model**: llama3.3:70b (42 GB, temperature 0.1 for maximum determinism)
- **Usage**: `ollama run transcriber-reformat < input.txt > output.txt`
- **Helper Script**: `scripts/reformat-transcript.sh` (batch processing support)
- **Documentation**: `specs/001-paragraph-reformatter/`
- **Features**:
  - Identifies logical topic shifts and adds paragraph breaks
  - Preserves 100% of original content (no words added/removed/modified)
  - Handles technical content (code blocks, URLs, special characters)
  - Works with any text length (short notes to lengthy transcripts)
- **Validation**: Full test suite with preservation and quality checks

## Next Development Areas
- Enhanced error recovery
- Additional audio format support
- Configuration file support
- Progress indicators
- Logging improvements