# DJI Transcriber Script Specification

## Overview

This specification describes the requirements and implementation details for creating a bash script (`transcriber.sh`) that processes DJI audio recordings through a 3-stage pipeline: import, transcription, and AI enhancement.

## Purpose

Create an automated workflow that:
1. Extracts audio files from DJI recording devices
2. Converts audio to text using speech recognition
3. Enhances transcriptions using AI language models
4. Maintains organized file structure with processing state tracking

## System Requirements

### Dependencies
- **Bash 4.0+** - Script execution environment
- **parakeet-mlx** - Audio-to-text transcription engine
- **ollama** - AI language model runtime
- **transcriber:latest** - Ollama model for transcript enhancement

### Hardware Requirements
- **DJI Mic 2** or compatible audio device
- **macOS** with Apple Silicon (recommended for parakeet-mlx)
- **Storage space** for audio files and processing pipeline

### File System Requirements
- **Source**: `/Volumes/DJI_MIC2/` - DJI device mount point
- **Destination**: `~/Resources/Transcripts/` - Processing workspace

## Functional Specifications

### Core Functions

#### 1. `process_dji_audio()`
**Purpose**: Import and rename DJI audio files

**Input**: 
- Source directory: `/Volumes/DJI_MIC2/`
- Sequential subdirectories: `DJI_Audio_001`, `DJI_Audio_002`, etc.
- Audio files: `DJI_XX_YYYYMMDD_HHMMSS.WAV` format

**Processing**:
- Scan for all `DJI_Audio_*` directories
- Extract `.WAV` files from each directory
- Parse filename to extract date/time components
- Rename files from `DJI_01_20250702_175446.WAV` to `2025-07-02-17:54:46.WAV`
- Move files to `~/Resources/Transcripts/audio-unprocessed/`

**Output**:
- Renamed audio files in standardized timestamp format
- Progress reporting and error handling
- File processing statistics

**Error Handling**:
- Validate source directory existence
- Check for duplicate destination files
- Handle invalid filename patterns
- Report processing statistics

#### 2. `transcribe_audio_files()`
**Purpose**: Convert audio files to text transcriptions

**Input**:
- Audio files in `~/Resources/Transcripts/audio-unprocessed/`
- Format: `2025-07-02-17:54:46.WAV`

**Processing**:
- Execute `parakeet-mlx $filename --output-format txt --output-dir text-unprocessed`
- Move successfully processed audio files to `audio-processed/`
- Generate text files in `text-unprocessed/`

**Output**:
- Text transcription files: `2025-07-02-17:54:46.txt`
- Processed audio files moved to separate directory
- Processing statistics and error reports

**Error Handling**:
- Verify parakeet-mlx installation
- Handle transcription failures gracefully
- Track successful vs failed processing

#### 3. `process_transcripts()`
**Purpose**: Enhance transcriptions using AI language models

**Input**:
- Text files in `~/Resources/Transcripts/text-unprocessed/`
- Format: `2025-07-02-17:54:46.txt`

**Processing**:
- Execute `cat $filename | ollama run transcriber:latest | tee $output_file`
- Generate markdown files with prefix naming: `transcript-2025-07-02-17:54:46.md`
- Move processed text files to `text-processed/`

**Output**:
- Enhanced transcript files in markdown format
- Processed text files moved to separate directory
- Final processing statistics

**Error Handling**:
- Verify ollama installation and model availability
- Handle AI processing failures
- Track successful vs failed enhancements

#### 4. `usage()`
**Purpose**: Display comprehensive usage instructions

**Output**:
- Script description and workflow overview
- Step-by-step function descriptions
- Requirements and dependencies
- Usage examples

### Directory Structure Specification

```
~/Resources/Transcripts/
├── audio-unprocessed/     # Raw audio files from DJI device
├── audio-processed/       # Audio files that have been transcribed
├── text-unprocessed/      # Raw transcription text files
├── text-processed/        # Text files processed by AI
└── transcripts/           # Final enhanced markdown transcripts
```

### File Naming Conventions

#### Audio Files
- **Input Format**: `DJI_XX_YYYYMMDD_HHMMSS.WAV`
  - `XX` = Sequential number (01, 02, etc.)
  - `YYYYMMDD` = Date (20250702)
  - `HHMMSS` = Time (175446)

- **Output Format**: `YYYY-MM-DD-HH:MM:SS.WAV`
  - Example: `2025-07-02-17:54:46.WAV`

#### Text Files
- **Transcription**: `2025-07-02-17:54:46.txt`
- **Final Transcript**: `transcript-2025-07-02-17:54:46.md`

### Script Execution Modes

#### 1. Direct Execution
```bash
./transcriber.sh
```
- Executes all three functions sequentially
- Provides step-by-step progress reporting
- Handles errors gracefully with informative messages

#### 2. Function Sourcing
```bash
source transcriber.sh
process_dji_audio
transcribe_audio_files
process_transcripts
```
- Allows individual function execution
- Enables selective processing steps
- Provides flexibility for debugging and testing

## Implementation Details

### Error Handling Requirements

1. **Dependency Checking**:
   - Verify `parakeet-mlx` availability before transcription
   - Verify `ollama` availability before AI processing
   - Provide clear installation instructions on failure

2. **File System Validation**:
   - Check source directory existence
   - Validate file format patterns
   - Handle permission issues gracefully

3. **Process Tracking**:
   - Count total files processed
   - Track success/failure rates
   - Provide detailed progress reporting

### Progress Reporting

- **File-level Progress**: Show current file being processed
- **Step-level Progress**: Indicate current pipeline stage
- **Summary Statistics**: Display totals and success rates
- **Error Details**: Provide specific failure information

### Bash Script Structure

```bash
#!/bin/bash

# Function definitions
process_dji_audio() { ... }
transcribe_audio_files() { ... }
process_transcripts() { ... }
usage() { ... }

# Main execution logic
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Sequential execution with error handling
fi
```

### Regular Expression Patterns

- **DJI Filename**: `^DJI_[0-9]+_([0-9]{8})_([0-9]{6})\.WAV$`
- **Date Extraction**: `BASH_REMATCH[1]` for date component
- **Time Extraction**: `BASH_REMATCH[2]` for time component

### Command Integration

#### Parakeet MLX Integration
```bash
parakeet-mlx "$wav_file" --output-format txt --output-dir "$text_dir"
```

#### Ollama Integration
```bash
cat "$txt_file" | ollama run transcriber:latest | tee "$transcript_file"
```

## Testing Considerations

### Test Cases

1. **Happy Path Testing**:
   - Complete pipeline with valid DJI files
   - Verify correct file naming and directory structure
   - Confirm all processing steps complete successfully

2. **Error Condition Testing**:
   - Missing dependencies (parakeet-mlx, ollama)
   - Invalid file formats
   - Disk space limitations
   - Permission issues

3. **Edge Cases**:
   - Empty directories
   - Duplicate files
   - Interrupted processing
   - Network connectivity issues (for ollama)

### Validation Criteria

- **File Integrity**: Verify all files are moved correctly
- **Naming Convention**: Confirm timestamp parsing accuracy
- **Processing State**: Ensure files move through pipeline correctly
- **Error Recovery**: Validate graceful failure handling

## Security Considerations

- **Path Validation**: Ensure file paths are properly sanitized
- **Permission Handling**: Manage file system permissions appropriately
- **Resource Management**: Prevent resource exhaustion during processing
- **Error Information**: Avoid exposing sensitive system information

## Performance Considerations

- **Batch Processing**: Handle multiple files efficiently
- **Resource Usage**: Monitor memory and CPU usage during processing
- **Storage Management**: Manage disk space during file movement
- **Progress Feedback**: Provide responsive user feedback

## Maintenance and Extensibility

### Configuration Options
- Configurable directory paths
- Customizable naming patterns
- Adjustable processing parameters

### Future Enhancements
- Support for additional audio formats
- Integration with other transcription services
- Batch processing optimizations
- GUI interface development

## Documentation Requirements

- **Inline Comments**: Document complex regex patterns and logic
- **Function Documentation**: Describe parameters and return values
- **Usage Examples**: Provide clear usage demonstrations
- **Error Messages**: Include helpful error resolution guidance

This specification provides the complete blueprint for implementing the DJI Transcriber script with all required functionality, error handling, and extensibility considerations. 