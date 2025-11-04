#!/usr/bin/env python3
# ============================================================
# TTS Provider Base Class
# Base class for all TTS providers
# ============================================================

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json

class TTSProvider(ABC):
    """
    Base class for all TTS providers.
    Extended from the original TTSProvider with metadata and directory structure support.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.sample_rate = self.config.get('sample_rate', None)
        self.language = self.config.get('language', 'vi')
        self.supported_voices = self._get_supported_voices()
        self.logger = logging.getLogger(f"TTSProvider.{self.name}")

        # Metadata info
        self.provider_info = {
            'name': self.name,
            'supported_voices': self.supported_voices,
            'sample_rate': self.sample_rate,
            'language': self.language,
            'config': self.config
        }

    @abstractmethod
    def _get_supported_voices(self) -> List[str]:
        """Get the list of voices supported by this provider"""
        pass

    @abstractmethod
    def synthesize(self, text: str, voice: str, output_file: Path) -> bool:
        """Synthesize audio from text and save to output_file"""
        pass

    def clone(self, text: str, reference_audio: Path, output_file: Path):
        """
        Clone voice from reference audio.
        Providers that don't support this should raise NotImplementedError.
        """
        raise NotImplementedError(f"Clone method not implemented for provider {self.name}")

    def get_metadata_info(self) -> Dict[str, Any]:
        """Get metadata information for this provider"""
        return self.provider_info.copy()

    def validate_text(self, text: str) -> bool:
        """Validate text before synthesizing"""
        if not text or not isinstance(text, str):
            return False
        if len(text.strip()) == 0:
            return False
        return True

    def estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on text length"""
        # Adjust parameters based on provider characteristics
        chars_per_second = self.config.get('chars_per_second', 12)
        estimated_seconds = len(text) / chars_per_second

        # Apply reasonable limits
        min_duration = self.config.get('min_duration', 0.5)
        max_duration = self.config.get('max_duration', 10.0)

        return max(min_duration, min(max_duration, estimated_seconds))

    def get_file_info(self, output_file: Path) -> Dict[str, Any]:
        """Get information about the output file after synthesizing"""
        if not output_file.exists():
            return {}

        try:
            stat = output_file.stat()
            return {
                'file_path': str(output_file),
                'file_size': stat.st_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime
            }
        except Exception as e:
            self.logger.warning(f"Cannot get file info for {output_file}: {e}")
            return {}

    def synthesize_with_metadata(self, text: str, voice: str, output_file: Path) -> Dict[str, Any]:
        """
        Synthesize with comprehensive metadata information.
        Returns a dict containing results and metadata.
        """
        result = {
            'success': False,
            'text': text,
            'voice': voice,
            'output_file': str(output_file),
            'provider': self.name,
            'sample_rate': self.sample_rate,
            'language': self.language,
            'estimated_duration': self.estimate_duration(text),
            'error': None,
            'file_info': {}
        }

        try:
            # Validate text
            if not self.validate_text(text):
                result['error'] = "Invalid text input"
                return result

            # Validate voice
            if voice not in self.supported_voices:
                result['error'] = f"Voice '{voice}' is not supported. Available voices: {self.supported_voices}"
                return result

            # Synthesize
            success = self.synthesize(text, voice, output_file)

            if success:
                result['success'] = True
                result['file_info'] = self.get_file_info(output_file)
                self.logger.info(f"✅ Synthesis successful: {output_file}")
            else:
                result['error'] = "Synthesis failed"

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Synthesis error: {e}")

        return result

    def synthesize_batch(self, text_file: Path, voice: str, output_dir: Path) -> Dict[str, Any]:
        """
        Synthesize multiple texts from a file.
        Default implementation raises NotImplementedError for providers that don't support batch processing.
        """
        raise NotImplementedError(f"Batch synthesis not implemented for provider {self.name}")

    def clone_batch(self, text_file: Path, reference_audio: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Clone voice and synthesize multiple texts from a file.
        Default implementation raises NotImplementedError for providers that don't support batch processing.
        """
        raise NotImplementedError(f"Batch cloning not implemented for provider {self.name}")


class ProviderCapabilities:
    """Class containing provider capability information"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.supports_cloning = False
        self.supports_streaming = False
        self.supports_batch = False
        self.max_text_length = 4000  # characters
        self.supported_languages = ['vi']
        self.supported_formats = ['wav', 'mp3']
        self.rate_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            'provider_name': self.provider_name,
            'supports_cloning': self.supports_cloning,
            'supports_streaming': self.supports_streaming,
            'supports_batch': self.supports_batch,
            'max_text_length': self.max_text_length,
            'supported_languages': self.supported_languages,
            'supported_formats': self.supported_formats,
            'rate_limits': self.rate_limits
        }
    """Class containing provider capability information"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.supports_cloning = False
        self.supports_streaming = False
        self.supports_batch = False
        self.max_text_length = 4000  # characters
        self.supported_languages = ['vi']
        self.supported_formats = ['wav', 'mp3']
        self.rate_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            'provider_name': self.provider_name,
            'supports_cloning': self.supports_cloning,
            'supports_streaming': self.supports_streaming,
            'supports_batch': self.supports_batch,
            'max_text_length': self.max_text_length,
            'supported_languages': self.supported_languages,
            'supported_formats': self.supported_formats,
            'rate_limits': self.rate_limits
        }
