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
from ...schemas.provider import ProviderConfig, VoiceConfig, AudioConfig

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

        # Optional ProviderConfig (minimal schema)
        self.provider_config: Optional[ProviderConfig] = None
        try:
            cfg_data = self.config.get('provider_config')
            if isinstance(cfg_data, ProviderConfig):
                self.provider_config = cfg_data
            elif isinstance(cfg_data, dict):
                # Validate and store
                self.provider_config = ProviderConfig.model_validate(cfg_data)
        except Exception as e:
            self.logger.warning(f"provider_config validation failed: {e}")

    @property
    def provider_info(self) -> Dict[str, Any]:
        """
        Build provider info dynamically to avoid having to enumerate keys.
        - Includes simple public attributes automatically (name, language, sample_rate, supported_voices, ...)
        - Always includes the raw config dict
        - If ProviderConfig is available, exposes its models and default_model
        """
        simple_types = (str, int, float, bool, list, dict, type(None))
        info: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if k.startswith('_'):
                continue
            if k in ('logger', 'key_manager', 'client'):
                # Skip heavy/runtime objects
                continue
            if isinstance(v, simple_types):
                info[k] = v

        # Ensure config is always present
        info['config'] = self.config

        # Add schema-derived fields if available
        if self.provider_config:
            try:
                info['models'] = getattr(self.provider_config, 'models', None)
                info['default_model'] = getattr(self.provider_config, 'default_model', None)
            except Exception:
                pass

        return info

    @abstractmethod
    def _get_supported_voices(self) -> List[str]:
        """Get the list of voices supported by this provider"""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_file: Path,
        voice_config: Optional[VoiceConfig] = None,
        audio_config: Optional[AudioConfig] = None,
    ) -> bool:
        """Synthesize audio from text and save to output_file.

        Args:
            text: The text to synthesize
            output_file: Where to save the synthesized audio
            voice_config: Optional voice configuration (voice_id, volume, speed, pitch, emotion)
            audio_config: Optional audio configuration (encoding, container, bit_rate, sample_rate, channel)

        Returns:
            bool: True if synthesis succeeded
        """
        pass

    def clone(self, text: str, reference_audio: Path, output_file: Path):
        """
        Clone voice from reference audio.
        Providers that don't support this should raise NotImplementedError.
        """
        raise NotImplementedError(f"Clone method not implemented for provider {self.name}")

    def get_metadata_info(self) -> Dict[str, Any]:
        """Get metadata information for this provider"""
        # Return a shallow copy to prevent external mutation
        return dict(self.provider_info)

    def validate_text(self, text: str) -> bool:
        """Validate text before synthesizing"""
        if not text or not isinstance(text, str):
            return False
        if len(text.strip()) == 0:
            return False
        return True

    

    def synthesize_with_metadata(self, text: str, voice: str, output_file: Path):
        """
        Synthesize with comprehensive metadata information.
        Returns a SynthesisResult instance.
        """
        from speech_synth_engine.schemas.schemas import SynthesisResult
        try:
            # Validate text
            if not self.validate_text(text):
                return SynthesisResult(
                    success=False,
                    text=text,
                    output_file=None,
                    provider=self.name,
                    error={'message': 'Invalid text input'}
                )
            # Validate voice
            if voice not in self.supported_voices:
                return SynthesisResult(
                    success=False,
                    text=text,
                    output_file=None,
                    provider=self.name,
                    error={'message': f"Voice '{voice}' is not supported. Available voices: {self.supported_voices}"}
                )
            # Synthesize using the abstract signature (text, output_file, voice_config, audio_config)
            voice_cfg = VoiceConfig(voice_id=voice) if isinstance(voice, str) else voice
            success = self.synthesize(text=text, output_file=output_file, voice_config=voice_cfg, audio_config=None)
            if success:
                return SynthesisResult(
                    success=True,
                    text=text,
                    output_file=str(output_file),
                    provider=self.name
                )
            else:
                return SynthesisResult(
                    success=False,
                    text=text,
                    output_file=None,
                    provider=self.name,
                    error={'message': 'Synthesis failed'}
                )
        except Exception as e:
            self.logger.error(f"❌ Synthesis error: {e}")
            return SynthesisResult(
                success=False,
                text=text,
                output_file=None,
                provider=self.name,
                error={'message': 'Synthesis error', 'detail': str(e)}
            )


    def clone_with_metadata(
        self,
        text: str,
        output_file: Path,
        voice_cloning_config: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Clone voice with comprehensive metadata information.

        This base implementation supports two common clone() signatures across providers:
        - clone(text, output_file, voice_cloning_config=...)
        - clone(text, reference_audio: Path, output_file)

        Providers can override this method for provider-specific behavior.
        """
        result = {
            'success': False,
            'text': text,
            'output_file': None,
            'provider': self.name,
            'sample_rate': self.sample_rate,
            'language': self.language,
            'effective_voice_config': {}
        }

        # Extract effective voice config (best-effort)
        try:
            vc = getattr(voice_cloning_config, 'voice_config', None) if voice_cloning_config else None
            if vc is not None:
                result['effective_voice_config'] = {
                    'reference_audio': getattr(vc, 'reference_audio', None),
                    'reference_text': getattr(vc, 'reference_text', None),
                    'enhance_speech': getattr(vc, 'enhance_speech', False),
                    'language': getattr(vc, 'language', None),
                }
        except Exception:
            pass

        try:
            # Validate text
            if not self.validate_text(text):
                result['error'] = "Invalid text input"
                return result

            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)

            # Try provider-specific clone(text, output_file, voice_cloning_config=...)
            success = False
            try:
                success = self.clone(text=text, output_file=output_file, voice_cloning_config=voice_cloning_config)  # type: ignore[call-arg]
            except TypeError:
                # Fallback to clone(text, reference_audio, output_file)
                ref_audio = None
                if voice_cloning_config is not None:
                    vc = getattr(voice_cloning_config, 'voice_config', None)
                    ref_audio = getattr(vc, 'reference_audio', None) if vc is not None else None
                if not ref_audio:
                    raise ValueError("reference_audio is required for cloning")
                success = self.clone(text, Path(ref_audio), output_file)  # type: ignore[misc]

            if success:
                result['success'] = True
                result['output_file'] = str(Path(output_file).absolute())
                return result

            result['error'] = {'message': 'Voice cloning failed'}
            return result

        except NotImplementedError as e:
            result['error'] = {'message': 'Clone not implemented', 'detail': str(e)}
            self.logger.error(f"❌ Clone not implemented: {e}")
            return result
        except Exception as e:
            result['error'] = {'message': 'Clone error', 'detail': str(e)}
            self.logger.error(f"❌ Clone error: {e}")
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
