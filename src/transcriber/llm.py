"""LLM processing providers."""

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessResult:
    """Result of LLM processing operation."""

    input_file: Path
    output_file: Path | None
    success: bool
    error: str | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available on the system."""
        ...

    @abstractmethod
    def process(self, input_file: Path, output_file: Path) -> ProcessResult:
        """Process a text file through the LLM.

        Args:
            input_file: Path to input text file
            output_file: Path for output file

        Returns:
            ProcessResult with outcome
        """
        ...


class OllamaProvider(LLMProvider):
    """LLM processing using Ollama."""

    def __init__(self, model: str) -> None:
        self.model = model

    def is_available(self) -> bool:
        """Check if ollama is installed."""
        return shutil.which("ollama") is not None

    def process(self, input_file: Path, output_file: Path) -> ProcessResult:
        """Process text through ollama model.

        Args:
            input_file: Path to input text file
            output_file: Path for output markdown file

        Returns:
            ProcessResult with outcome
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Read input file
            input_text = input_file.read_text()

            # Run ollama
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=input_text,
                capture_output=True,
                text=True,
                check=True,
            )

            # Write output
            output_file.write_text(result.stdout)

            return ProcessResult(
                input_file=input_file,
                output_file=output_file,
                success=True,
            )

        except subprocess.CalledProcessError as e:
            return ProcessResult(
                input_file=input_file,
                output_file=None,
                success=False,
                error=f"ollama failed: {e.stderr}",
            )
        except FileNotFoundError:
            return ProcessResult(
                input_file=input_file,
                output_file=None,
                success=False,
                error="ollama not found",
            )

    def classify(self, prompt: str) -> subprocess.CompletedProcess[str]:
        """Send a classification prompt to ollama.

        Args:
            prompt: The classification prompt text.

        Returns:
            CompletedProcess with stdout containing the LLM response.
        """
        return subprocess.run(
            ["ollama", "run", self.model],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )


def get_llm_provider(provider_name: str, model: str) -> LLMProvider:
    """Get an LLM provider by name.

    Args:
        provider_name: Name of provider ("ollama", "claude")
        model: Model name for the provider

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider_name == "ollama":
        return OllamaProvider(model=model)

    raise ValueError(f"Unknown LLM provider: {provider_name}")
