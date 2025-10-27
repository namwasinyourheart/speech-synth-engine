from abc import ABC, abstractmethod
from pathlib import Path

class TTSProvider(ABC):
    """
    Abstract base class for all TTS providers.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def synthesize(self, text: str, voice: str, output_file: Path):
        """Synthesize audio from text"""
        pass

    def clone(self, text: str, reference_audio: Path, output_file: Path):
        """
        Clone voice from reference audio.
        Provider which does not support cloning will raise NotImplementedError.
        """
        raise NotImplementedError(f"Clone method is not implemented for provider {self.name}")
