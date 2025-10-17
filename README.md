# DJI Transcriber

A complete pipeline for processing DJI audio recordings into formatted transcripts using automated speech recognition and AI enhancement.

## Overview

This tool provides a 3-step automated workflow:
1. **Import & Rename** - Extract audio files from DJI device and rename with timestamps
2. **Transcribe** - Convert audio to text using Parakeet MLX
3. **Process** - Enhance transcripts using Ollama AI

## Features

- 🎤 **DJI Audio Support** - Automatically processes DJI Mic 2 recordings
- 📁 **Smart File Management** - Organized directory structure with processed file tracking
- 🔄 **Automated Pipeline** - Run all steps with a single command
- 📝 **AI Enhancement** - Polish transcripts using Ollama AI models
- ⚡ **Batch Processing** - Handle multiple recordings simultaneously
- 🛡️ **Error Handling** - Comprehensive error checking and recovery

## Prerequisites

### Required Software

1. **Parakeet MLX** - For audio transcription
   ```bash
   pip install parakeet-mlx
   ```

2. **Ollama** - For transcript processing
   ```bash
   # Install Ollama (visit https://ollama.com for installation instructions)
   
   # Create the custom transcriber model using the provided Modelfile
   ollama create transcriber -f Modelfile
   ```
   
   **Note**: The `transcriber` model is a custom model built from the included `Modelfile` that specializes in formatting speech-to-text transcriptions into well-structured markdown documents. It's based on Qwen2.5:72b-instruct with specific instructions for handling technical terminology and organizing transcribed content.

### Hardware Requirements

- **DJI Mic 2** or compatible DJI audio device
- **Mac with Apple Silicon** (for Parakeet MLX optimal performance)
- **Sufficient storage** for audio files and transcripts

## Installation

1. Clone or download this repository
2. Make the script executable:
   ```bash
   chmod +x transcriber.sh
   ```

## Usage

### Quick Start (Complete Pipeline)

```bash
# Run the complete pipeline
./transcriber.sh
```

This will automatically:
1. Import audio files from your DJI device
2. Transcribe them to text
3. Process them through AI for enhancement

### Manual Step-by-Step

```bash
# Load the functions
source transcriber.sh

# Step 1: Import and rename DJI audio files
process_dji_audio

# Step 2: Transcribe audio files
transcribe_audio_files

# Step 3: Process transcripts through Ollama
process_transcripts
```

## Directory Structure

The script creates and manages the following directory structure:

```
~/Resources/Transcripts/
├── audio-unprocessed/     # Raw audio files from DJI device
├── audio-processed/       # Audio files that have been transcribed
├── text-unprocessed/      # Raw transcription text files
├── text-processed/        # Text files processed by Ollama
└── transcripts/           # Final enhanced markdown transcripts
```

## File Naming Convention

### Audio Files
- **Input**: `DJI_01_20250702_175446.WAV`
- **Output**: `2025-07-02-17:54:46.WAV`

### Transcript Files
- **Final Output**: `transcript-2025-07-02-17:54:46.md`

## Workflow Details

### Step 1: Import & Rename (`process_dji_audio`)

- Scans `/Volumes/DJI_MIC2/` for `DJI_Audio_*` directories
- Extracts `.WAV` files and renames them with ISO timestamp format
- Moves files to `~/Resources/Transcripts/audio-unprocessed/`

### Step 2: Transcribe (`transcribe_audio_files`)

- Uses Parakeet MLX to convert audio to text
- Generates `.txt` files in `~/Resources/Transcripts/text-unprocessed/`
- Moves processed audio to `~/Resources/Transcripts/audio-processed/`

### Step 3: Process (`process_transcripts`)

- Enhances transcripts using Ollama's `transcriber:latest` model
- Generates final markdown files in `~/Resources/Transcripts/transcripts/`
- Moves processed text files to `~/Resources/Transcripts/text-processed/`

## Example Output

```bash
$ ./transcriber.sh
Starting DJI Audio File Processor & Transcriber...

STEP 1: Processing DJI audio files...
=======================================
Processing directory: DJI_Audio_001
Processing file: DJI_01_20250702_175446.WAV
✓ Moved: DJI_01_20250702_175446.WAV -> 2025-07-02-17:54:46.WAV

STEP 2: Transcribing audio files...
====================================
Found 1 .WAV files to transcribe
Processing: 2025-07-02-17:54:46.WAV
✓ Transcription successful for: 2025-07-02-17:54:46.WAV

STEP 3: Processing transcripts through ollama...
================================================
Found 1 .txt files to process through ollama
Processing: 2025-07-02-17:54:46.txt
✓ Transcript generated: transcript-2025-07-02-17:54:46.md
```

## Troubleshooting

### Common Issues

1. **"parakeet-mlx command not found"**
   - Install Parakeet MLX: `pip install parakeet-mlx`

2. **"ollama command not found"**
   - Install Ollama from https://ollama.com
   - Install the transcriber model: `ollama pull transcriber:latest`

3. **"Source directory not found"**
   - Ensure your DJI device is connected and mounted at `/Volumes/DJI_MIC2/`

4. **"No DJI_Audio_* directories found"**
   - Check that your DJI device has recorded audio files
   - Verify the device is properly mounted

### Getting Help

```bash
# View usage information
./transcriber.sh --help

# Or source the script and run
source transcriber.sh
usage
```

## Advanced Usage

### Processing Specific Steps

You can run individual steps as needed:

```bash
source transcriber.sh

# Only import audio files
process_dji_audio

# Only transcribe (if audio files already imported)
transcribe_audio_files

# Only process transcripts (if text files already generated)
process_transcripts
```

### Paragraph Reformatter (Optional)

The `transcriber-reformat` model is an optional tool for reformatting raw transcription text into well-structured paragraphs. This is useful when you have continuous text from speech-to-text output that lacks proper paragraph breaks.

**Setup:**
```bash
# Create the reformatter model (one-time setup)
ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat
```

**Usage:**
```bash
# Reformat a transcript file
ollama run transcriber-reformat < input.txt > output.txt

# Or process files from the pipeline
ollama run transcriber-reformat < ~/Resources/Transcripts/text-unprocessed/2025-07-02-17:54:46.txt > reformatted.txt
```

**Features:**
- Identifies logical topic shifts and natural content breaks
- Adds paragraph breaks while preserving 100% of original content
- Handles technical content (URLs, code blocks, special characters)
- Works with text of any length (short notes to lengthy transcripts)
- Temperature: 0.1 for maximum consistency

**Important:** The reformatter ONLY adds paragraph breaks - it never modifies, adds, or removes words. All original content is preserved exactly.

### Customizing Ollama Model

Edit the script to use a different Ollama model:

```bash
# Change this line in the process_transcripts function
ollama run your-custom-model:latest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for personal and educational use.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the error messages carefully
3. Ensure all prerequisites are installed
4. Verify your DJI device is properly connected 