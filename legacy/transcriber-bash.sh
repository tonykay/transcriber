#!/bin/bash

# Function to move and rename DJI audio files
# Usage: process_dji_audio
process_dji_audio() {
    local source_base="/Volumes/DJI_MIC2"
    local dest_dir="$HOME/Resources/Transcripts/audio-unprocessed"
    
    # Create destination directory if it doesn't exist
    mkdir -p "$dest_dir"
    
    # Check if source directory exists
    if [[ ! -d "$source_base" ]]; then
        echo "Error: Source directory $source_base not found"
        return 1
    fi
    
    # Find all DJI_Audio_* directories
    local audio_dirs=($(find "$source_base" -maxdepth 1 -type d -name "DJI_Audio_*" | sort))
    
    if [[ ${#audio_dirs[@]} -eq 0 ]]; then
        echo "No DJI_Audio_* directories found in $source_base"
        return 1
    fi
    
    local total_files=0
    local processed_files=0
    
    # Process each audio directory
    for audio_dir in "${audio_dirs[@]}"; do
        echo "Processing directory: $(basename "$audio_dir")"
        
        # Find all .WAV files in the directory
        while IFS= read -r -d '' file; do
            ((total_files++))
            
            local filename=$(basename "$file")
            echo "Processing file: $filename"
            
            # Check if filename matches DJI pattern: DJI_XX_YYYYMMDD_HHMMSS.WAV
            if [[ $filename =~ ^DJI_[0-9]+_([0-9]{8})_([0-9]{6})\.WAV$ ]]; then
                local date_part="${BASH_REMATCH[1]}"
                local time_part="${BASH_REMATCH[2]}"
                
                # Extract date components: YYYYMMDD -> YYYY-MM-DD
                local year="${date_part:0:4}"
                local month="${date_part:4:2}"
                local day="${date_part:6:2}"
                
                # Extract time components: HHMMSS -> HH:MM:SS
                local hour="${time_part:0:2}"
                local minute="${time_part:2:2}"
                local second="${time_part:4:2}"
                
                # Create new filename: YYYY-MM-DD-HH:MM:SS.WAV
                local new_filename="${year}-${month}-${day}-${hour}:${minute}:${second}.WAV"
                local dest_file="$dest_dir/$new_filename"
                
                # Check if destination file already exists
                if [[ -f "$dest_file" ]]; then
                    echo "Warning: Destination file $new_filename already exists, skipping..."
                    continue
                fi
                
                # Move and rename the file
                if mv "$file" "$dest_file"; then
                    echo "✓ Moved: $filename -> $new_filename"
                    ((processed_files++))
                else
                    echo "✗ Failed to move: $filename"
                fi
            else
                echo "Warning: Filename $filename doesn't match expected DJI pattern, skipping..."
            fi
        done < <(find "$audio_dir" -maxdepth 1 -type f -name "*.WAV" -print0)
    done
    
    echo ""
    echo "Summary:"
    echo "Total files found: $total_files"
    echo "Files processed: $processed_files"
    echo "Files moved to: $dest_dir"
    
    if [[ $processed_files -gt 0 ]]; then
        echo ""
        echo "Processed files in destination directory:"
        ls -la "$dest_dir"
    fi
}

# Function to transcribe audio files and move processed files
# Usage: transcribe_audio_files
transcribe_audio_files() {
    local audio_dir="$HOME/Resources/Transcripts/audio-unprocessed"
    local processed_dir="$HOME/Resources/Transcripts/audio-processed"
    local text_dir="$HOME/Resources/Transcripts/text-unprocessed"
    
    # Create directories if they don't exist
    mkdir -p "$processed_dir"
    mkdir -p "$text_dir"
    
    # Check if audio directory exists
    if [[ ! -d "$audio_dir" ]]; then
        echo "Error: Audio directory $audio_dir not found"
        echo "Run process_dji_audio first to move audio files from DJI device"
        return 1
    fi
    
    # Find all .WAV files in the audio directory
    local wav_files=($(find "$audio_dir" -maxdepth 1 -type f -name "*.WAV" | sort))
    
    if [[ ${#wav_files[@]} -eq 0 ]]; then
        echo "No .WAV files found in $audio_dir"
        return 1
    fi
    
    # Check if parakeet-mlx is available
    if ! command -v parakeet-mlx &> /dev/null; then
        echo "Error: parakeet-mlx command not found"
        echo "Please install parakeet-mlx before running this function"
        return 1
    fi
    
    local total_files=${#wav_files[@]}
    local processed_files=0
    local failed_files=0
    
    echo "Found $total_files .WAV files to transcribe"
    echo "Starting transcription process..."
    echo ""
    
    # Process each WAV file
    for wav_file in "${wav_files[@]}"; do
        local filename=$(basename "$wav_file")
        echo "Processing: $filename"
        
        # Run parakeet-mlx transcription
        if parakeet-mlx "$wav_file" --output-format txt --output-dir "$text_dir"; then
            echo "✓ Transcription successful for: $filename"
            
            # Move processed file to audio-processed directory
            local processed_file="$processed_dir/$filename"
            if mv "$wav_file" "$processed_file"; then
                echo "✓ Moved to processed: $filename"
                ((processed_files++))
            else
                echo "✗ Failed to move processed file: $filename"
                ((failed_files++))
            fi
        else
            echo "✗ Transcription failed for: $filename"
            ((failed_files++))
        fi
        
        echo ""
    done
    
    echo "Transcription Summary:"
    echo "Total files: $total_files"
    echo "Successfully processed: $processed_files"
    echo "Failed: $failed_files"
    echo ""
    echo "Processed audio files moved to: $processed_dir"
    echo "Transcription text files saved to: $text_dir"
    
    if [[ $processed_files -gt 0 ]]; then
        echo ""
        echo "Processed audio files:"
        ls -la "$processed_dir"
        echo ""
        echo "Generated text files:"
        ls -la "$text_dir"
    fi
}

# Function to process transcriptions through ollama
# Usage: process_transcripts
process_transcripts() {
    local text_dir="$HOME/Resources/Transcripts/text-unprocessed"
    local processed_text_dir="$HOME/Resources/Transcripts/text-processed"
    local transcripts_dir="$HOME/Resources/Transcripts/transcripts"
    
    # Create directories if they don't exist
    mkdir -p "$processed_text_dir"
    mkdir -p "$transcripts_dir"
    
    # Check if text directory exists
    if [[ ! -d "$text_dir" ]]; then
        echo "Error: Text directory $text_dir not found"
        echo "Run transcribe_audio_files first to generate text files"
        return 1
    fi
    
    # Find all .txt files in the text directory
    local txt_files=($(find "$text_dir" -maxdepth 1 -type f -name "*.txt" | sort))
    
    if [[ ${#txt_files[@]} -eq 0 ]]; then
        echo "No .txt files found in $text_dir"
        return 1
    fi
    
    # Check if ollama is available
    if ! command -v ollama &> /dev/null; then
        echo "Error: ollama command not found"
        echo "Please install ollama before running this function"
        return 1
    fi
    
    local total_files=${#txt_files[@]}
    local processed_files=0
    local failed_files=0
    
    echo "Found $total_files .txt files to process through ollama"
    echo "Starting transcript processing..."
    echo ""
    
    # Process each txt file
    for txt_file in "${txt_files[@]}"; do
        local filename=$(basename "$txt_file")
        local base_name="${filename%.txt}"
        local transcript_file="$transcripts_dir/transcript-${base_name}.md"
        
        echo "Processing: $filename"
        
        # Run ollama transcription
        if cat "$txt_file" | ollama run transcriber:latest | tee "$transcript_file"; then
            echo "✓ Transcript generated: transcript-${base_name}.md"
            
            # Move processed txt file to text-processed directory
            local processed_file="$processed_text_dir/$filename"
            if mv "$txt_file" "$processed_file"; then
                echo "✓ Moved to processed: $filename"
                ((processed_files++))
            else
                echo "✗ Failed to move processed text file: $filename"
                ((failed_files++))
            fi
        else
            echo "✗ Transcript processing failed for: $filename"
            ((failed_files++))
        fi
        
        echo ""
    done
    
    echo "Transcript Processing Summary:"
    echo "Total files: $total_files"
    echo "Successfully processed: $processed_files"
    echo "Failed: $failed_files"
    echo ""
    echo "Processed text files moved to: $processed_text_dir"
    echo "Final transcripts saved to: $transcripts_dir"
    
    if [[ $processed_files -gt 0 ]]; then
        echo ""
        echo "Processed text files:"
        ls -la "$processed_text_dir"
        echo ""
        echo "Generated transcript files:"
        ls -la "$transcripts_dir"
    fi
}

# Function to show usage
usage() {
    echo "DJI Audio File Processor & Transcriber"
    echo ""
    echo "Usage:"
    echo "  source transcriber.sh"
    echo "  process_dji_audio        # Step 1: Import and rename audio files"
    echo "  transcribe_audio_files   # Step 2: Transcribe audio files"
    echo "  process_transcripts      # Step 3: Process transcripts through ollama"
    echo ""
    echo "Step 1 - process_dji_audio:"
    echo "  - Find all DJI_Audio_* directories in /Volumes/DJI_MIC2/"
    echo "  - Move .WAV files to ~/Resources/Transcripts/audio-unprocessed/"
    echo "  - Rename files from DJI_XX_YYYYMMDD_HHMMSS.WAV to YYYY-MM-DD-HH:MM:SS.WAV"
    echo ""
    echo "Step 2 - transcribe_audio_files:"
    echo "  - Transcribe .WAV files using parakeet-mlx"
    echo "  - Save transcriptions to ~/Resources/Transcripts/text-unprocessed/"
    echo "  - Move processed audio files to ~/Resources/Transcripts/audio-processed/"
    echo ""
    echo "Step 3 - process_transcripts:"
    echo "  - Process .txt files through ollama transcriber:latest"
    echo "  - Save final transcripts to ~/Resources/Transcripts/transcripts/"
    echo "  - Move processed text files to ~/Resources/Transcripts/text-processed/"
    echo ""
    echo "Requirements:"
    echo "  - parakeet-mlx must be installed for transcription"
    echo "  - ollama and transcriber:latest model must be installed for transcript processing"
}

# If script is executed directly (not sourced), run the functions
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Starting DJI Audio File Processor & Transcriber..."
    echo ""
    
    # Step 1: Process DJI audio files
    echo "STEP 1: Processing DJI audio files..."
    echo "======================================="
    process_dji_audio
    
    # Check if any files were processed before proceeding
    if [[ $? -eq 0 ]]; then
        echo ""
        echo "STEP 2: Transcribing audio files..."
        echo "===================================="
        transcribe_audio_files
        
        # Check if transcription was successful before proceeding
        if [[ $? -eq 0 ]]; then
            echo ""
            echo "STEP 3: Processing transcripts through ollama..."
            echo "================================================"
            process_transcripts
        else
            echo ""
            echo "Skipping ollama processing due to errors in transcription."
            echo "To run ollama processing manually: source transcriber.sh && process_transcripts"
        fi
    else
        echo ""
        echo "Skipping transcription and ollama steps due to errors in audio processing."
        echo "To run manually: source transcriber.sh && transcribe_audio_files && process_transcripts"
    fi
fi 