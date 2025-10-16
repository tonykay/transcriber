# CLAUDE.md - Development Context

## Project Overview
DJI Transcriber - A complete pipeline for processing DJI audio recordings into formatted transcripts using automated speech recognition and AI enhancement.

## Architecture
- **Language**: Bash shell script
- **Main Script**: `transcriber.sh` (executable)
- **Dependencies**:
  - Parakeet MLX (speech-to-text)
  - Ollama with custom `transcriber` model (text enhancement)

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

## Next Development Areas
- Enhanced error recovery
- Additional audio format support
- Configuration file support
- Progress indicators
- Logging improvements