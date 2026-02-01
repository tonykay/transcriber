"""Pipeline orchestration for transcription workflow."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from transcriber.audio import import_dji_audio
from transcriber.config import TranscriberConfig
from transcriber.llm import get_llm_provider
from transcriber.stt import get_stt_provider


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    audio_imported: int = 0
    audio_skipped: int = 0
    audio_failed: int = 0
    transcribed: int = 0
    transcribe_failed: int = 0
    processed: int = 0
    process_failed: int = 0

    @property
    def total_successful(self) -> int:
        """Count of fully processed transcripts."""
        return self.processed


class Pipeline:
    """Orchestrates the full transcription pipeline.

    The pipeline:
    1. Imports audio files from DJI device
    2. Transcribes audio to text using STT provider
    3. Processes transcripts through LLM for enhancement
    """

    def __init__(self, config: TranscriberConfig, console: Console | None = None):
        """Initialize pipeline with configuration.

        Args:
            config: Transcriber configuration
            console: Rich console for output (optional)
        """
        self.config = config
        self.console = console or Console()

    def run(self, skip_import: bool = False) -> PipelineResult:
        """Run the full pipeline.

        Args:
            skip_import: If True, skip the audio import step

        Returns:
            PipelineResult with counts of processed files
        """
        result = PipelineResult()

        # Step 1: Import audio from DJI device
        if not skip_import:
            imported, skipped, failed = self._import_audio()
            result.audio_imported = imported
            result.audio_skipped = skipped
            result.audio_failed = failed

        # Step 2: Transcribe audio files
        transcribed, transcribe_failed = self._transcribe_audio()
        result.transcribed = transcribed
        result.transcribe_failed = transcribe_failed

        # Step 3: Process transcripts through LLM
        processed, process_failed = self._process_transcripts()
        result.processed = processed
        result.process_failed = process_failed

        return result

    def _import_audio(self) -> tuple[int, int, int]:
        """Import audio files from DJI device.

        Returns:
            Tuple of (imported, skipped, failed) counts
        """
        self.console.print("\n[bold]Importing audio from DJI device...[/bold]")

        source = Path(self.config.paths.dji_source)
        dest = Path(self.config.paths.audio_unprocessed)

        result = import_dji_audio(source, dest, move=True)

        self.console.print(f"  Found: {result.total_found}")
        self.console.print(f"  Imported: {result.processed}")
        self.console.print(f"  Skipped: {result.skipped}")

        return result.processed, result.skipped, result.failed

    def _transcribe_audio(self) -> tuple[int, int]:
        """Transcribe unprocessed audio files.

        Returns:
            Tuple of (transcribed, failed) counts
        """
        self.console.print("\n[bold]Transcribing audio files...[/bold]")

        audio_dir = Path(self.config.paths.audio_unprocessed)
        text_dir = Path(self.config.paths.text_unprocessed)
        processed_audio_dir = Path(self.config.paths.audio_processed)

        # Ensure directories exist
        text_dir.mkdir(parents=True, exist_ok=True)
        processed_audio_dir.mkdir(parents=True, exist_ok=True)

        # Get STT provider
        provider = get_stt_provider(
            self.config.stt.provider,
            self.config.stt.model,
        )

        if not provider.is_available():
            self.console.print(
                f"  [red]STT provider '{self.config.stt.provider}' is not available[/red]"
            )
            return 0, 0

        # Find audio files to transcribe
        audio_files = list(audio_dir.glob("*.WAV"))
        if not audio_files:
            self.console.print("  No audio files to transcribe")
            return 0, 0

        transcribed = 0
        failed = 0

        for audio_file in audio_files:
            self.console.print(f"  Transcribing: {audio_file.name}")

            result = provider.transcribe(audio_file, text_dir)

            if result.success:
                # Move audio to processed directory
                shutil.move(str(audio_file), str(processed_audio_dir / audio_file.name))
                transcribed += 1
                self.console.print("    [green]Success[/green]")
            else:
                failed += 1
                self.console.print(f"    [red]Failed: {result.error}[/red]")

        self.console.print(f"  Transcribed: {transcribed}, Failed: {failed}")
        return transcribed, failed

    def _process_transcripts(self) -> tuple[int, int]:
        """Process transcripts through LLM.

        Returns:
            Tuple of (processed, failed) counts
        """
        self.console.print("\n[bold]Processing transcripts through LLM...[/bold]")

        text_dir = Path(self.config.paths.text_unprocessed)
        processed_text_dir = Path(self.config.paths.text_processed)
        output_dir = Path(self.config.paths.transcripts)

        # Ensure directories exist
        processed_text_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get LLM provider
        provider = get_llm_provider(
            self.config.llm.provider,
            self.config.llm.model,
        )

        if not provider.is_available():
            self.console.print(
                f"  [red]LLM provider '{self.config.llm.provider}' is not available[/red]"
            )
            return 0, 0

        # Find text files to process
        text_files = list(text_dir.glob("*.txt"))
        if not text_files:
            self.console.print("  No text files to process")
            return 0, 0

        processed = 0
        failed = 0

        for text_file in text_files:
            self.console.print(f"  Processing: {text_file.name}")

            # Output filename: transcript-{timestamp}.md
            output_file = output_dir / f"transcript-{text_file.stem}.md"

            result = provider.process(text_file, output_file)

            if result.success:
                # Move text to processed directory
                shutil.move(str(text_file), str(processed_text_dir / text_file.name))
                processed += 1
                self.console.print("    [green]Success[/green]")
            else:
                failed += 1
                self.console.print(f"    [red]Failed: {result.error}[/red]")

        self.console.print(f"  Processed: {processed}, Failed: {failed}")
        return processed, failed
