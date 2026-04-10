# Vietnamese voice id
# 0e58d60a-2f1a-4252-81bd-3db6af45fb41 (male_central)): Easygoing adult male voice with a friendly tone for light conversation, casual dialogue, and everyday chat
# b8cd71e3-bc14-4538-a530-d6314731c036 (femal_south): Soft-spoken adult female voice for calm conversations and customer support
# 935a9060-373c-49e4-b078-f4ea6326987a (female_north): Linh - Soft Presence Voice with gentle tone and natural warmth, perfect for natural conversations and friendly dialogue


# curl --location 'https://api.cartesia.ai/tts/bytes' \
# --header 'X-API-Key: sk_car_kyo1L9tkE8H6khB2eL1fTV' \
# --header 'Cartesia-Version: 2024-06-10' \
# --header 'Content-Type: application/json' \
# --data '
# {
#   "model_id": "sonic-3",
#   "transcript": "World Cup 2026 sẽ diễn ra từ ngày 11/6 đến 19/7 tại Mỹ, Mexico và Canada, với tổng cộng 16 thành phố đăng cai. Trận khai mạc giữa Mexico và Nam Phi diễn ra vào lúc 2h ngày 12/6 (theo giờ Việt Nam)",
#   "voice": {
#     "mode": "id",
#     "id": "b8cd71e3-bc14-4538-a530-d6314731c036"
#   },
#   "output_format": {
#     "container": "mp3",
#     "encoding": "pcm_f32le",
#     "sample_rate": 44100
#   },
#   "generation_config": {
#     "volume": 1,
#     "speed": 1,
#     "emotion": "neutral"
#   },
#   "language": "vi",
#   "speed": "normal",
#   "add_timestamps": false,
#   "add_phoneme_timestamps": false,
#   "use_normalized_timestamps": true
# }
# '

from __future__ import annotations

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

from .base.provider import TTSProvider
from speech_synth_engine.schemas.provider import VoiceConfig, AudioConfig, ProviderConfig
from .utils import resolve_api_key, extract_voice_params, extract_audio_params, validate_enum_value

# Load environment variables
load_dotenv()


class CartesiaTTSProvider(TTSProvider):
    """
    TTS provider using Cartesia API.
    
    Maps VoiceConfig/AudioConfig to Cartesia /tts/bytes JSON payload per cURL example.
    Supports Vietnamese voices with configurable model, sample rate, and audio format.
    """
    
    # Default generation parameters
    DEFAULT_VOLUME = 1.0
    DEFAULT_SPEED = 1.0
    DEFAULT_EMOTION = "neutral"
    
    # Provider defaults (no longer read from self.config)
    DEFAULT_API_BASE = "https://api.cartesia.ai"
    DEFAULT_API_VERSION = "2024-06-10"
    DEFAULT_MODEL = "sonic-3"
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_CONTAINER = "mp3"
    DEFAULT_ENCODING = "pcm_f32le"
    DEFAULT_LANGUAGE = "vi"
    
    # Cartesia API limits
    MAX_TEXT_LENGTH = 5000  # characters
    SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 24000, 32000, 44100]
    SUPPORTED_CONTAINERS = ["mp3", "wav", "raw"]
    SUPPORTED_ENCODINGS = ["pcm_f32le", "pcm_s16le", "pcm_mulaw", "pcm_alaw"]

    def __init__(self, name: str = "cartesia", provider_config: Optional[ProviderConfig] = None):
        # Initialize with provider_config for consistency with factory pattern
        super().__init__(name, {"provider_config": provider_config} if provider_config else {})

        self.logger = logging.getLogger(f"TTSProvider.{self.name}")

        # API configuration (use class defaults; allow model from ProviderConfig)
        self.api_base = self.DEFAULT_API_BASE
        self.api_version = self.DEFAULT_API_VERSION
        provider_cfg = getattr(self, 'provider_config', None)
        self.model_id = (
            (getattr(provider_cfg, 'default_model', None) if provider_cfg else None)
            or self.DEFAULT_MODEL
        )
        
        # Audio/language defaults (class constants only)
        self.sample_rate = self.DEFAULT_SAMPLE_RATE
        self.default_container = self.DEFAULT_CONTAINER
        self.default_encoding = self.DEFAULT_ENCODING
        self.language = self.DEFAULT_LANGUAGE
        
        # Track last error for detailed error reporting
        self.last_error: Optional[str] = None

        # Resolve API key using utility helper
        self.api_key = resolve_api_key(
            config={},
            provider_config=getattr(self, 'provider_config', None),
            fallback_env_var='CARTESIA_API_KEY'
        )
        
        if not self.api_key:
            raise ValueError(
                "No Cartesia API key provided. Specify 'api_keys' in config, "
                "or set via ProviderConfig.credentials.api_keys, "
                "or set CARTESIA_API_KEY environment variable."
            )

        self.logger.debug(
            f"Initialized Cartesia provider: model={self.model_id}, "
            f"sample_rate={self.sample_rate}, container={self.default_container}"
        )

    def _get_supported_voices(self) -> List[str]:
        """Return curated Vietnamese voice IDs for Cartesia."""
        return [
            "0e58d60a-2f1a-4252-81bd-3db6af45fb41",  # male_central
            "b8cd71e3-bc14-4538-a530-d6314731c036",  # female_south
            "935a9060-373c-49e4-b078-f4ea6326987a",  # female_north (Linh)
        ]

    @staticmethod
    def _http_post_bytes(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> bytes:
        """
        Perform HTTP POST using stdlib and return raw response bytes.
        
        Args:
            url: API endpoint URL
            headers: HTTP headers
            payload: JSON payload dict
            
        Returns:
            Raw response bytes
            
        Raises:
            RuntimeError: On HTTP or network errors
        """
        data = json.dumps(payload).encode('utf-8')
        req = Request(url, data=data, headers=headers, method='POST')
        
        try:
            with urlopen(req) as resp:
                return resp.read()
        except HTTPError as e:
            body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
            # Truncate long error messages
            body_preview = body[:500] + '...' if len(body) > 500 else body
            raise RuntimeError(f"HTTP {e.code}: {body_preview}")
        except URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")

    def synthesize(
        self,
        text: str,
        output_file: Path,
        generation_config: Optional[Any] = None,
    ) -> bool:
        """
        Synthesize audio from text and save to output_file using Cartesia /tts/bytes.
        
        Args:
            text: Text to synthesize
            output_file: Path to save the output audio file
            generation_config: Optional GenerationConfig providing model, voice_config, and audio_config
            
        Returns:
            True if synthesis succeeded, False otherwise
        """
        # Extract voice_config and audio_config from generation_config if provided
        voice_config = None
        audio_config = None
        if generation_config is not None:
            try:
                if getattr(generation_config, 'model', None):
                    self.model_id = generation_config.model
                voice_config = getattr(generation_config, 'voice_config', None)
                audio_config = getattr(generation_config, 'audio_config', None)
                if audio_config and getattr(audio_config, 'sample_rate', None):
                    self.sample_rate = audio_config.sample_rate
            except Exception:
                pass
        # Clear any previous error
        self.last_error = None
        
        try:
            if not self.validate_text(text):
                self.last_error = "Invalid text provided for synthesis"
                self.logger.error(self.last_error)
                return False

            # Validate text length
            if len(text) > self.MAX_TEXT_LENGTH:
                self.logger.warning(
                    f"Text length ({len(text)}) exceeds recommended limit ({self.MAX_TEXT_LENGTH})"
                )

            # Extract voice parameters using helper
            voice_params = extract_voice_params(
                voice_config,
                defaults={
                    'voice_id': None,
                    'language': self.language,
                    'volume': self.DEFAULT_VOLUME,
                    'speed': self.DEFAULT_SPEED,
                    'emotion': self.DEFAULT_EMOTION,
                }
            )
            
            # Resolve voice ID (fallback to default if not provided)
            voice_id = voice_params['voice_id']
            if not voice_id:
                supported = self._get_supported_voices()
                if not supported:
                    self.last_error = "No voice provided and no supported voices available"
                    self.logger.error(self.last_error)
                    return False
                voice_id = supported[0]
                self.logger.info(f"No voice specified, using default: {voice_id}")

            # Extract audio parameters using helper
            audio_params = extract_audio_params(
                audio_config,
                defaults={
                    'container': self.default_container,
                    'encoding': self.default_encoding,
                    'sample_rate': self.sample_rate,
                }
            )
            
            # Validate audio config
            validate_enum_value(
                audio_params['sample_rate'],
                self.SUPPORTED_SAMPLE_RATES,
                'Sample rate',
                self.logger
            )
            validate_enum_value(
                audio_params['container'],
                self.SUPPORTED_CONTAINERS,
                'Container',
                self.logger
            )

            # Build Cartesia API payload
            payload: Dict[str, Any] = {
                "model_id": self.model_id,
                "transcript": text,
                "voice": {
                    "mode": "id",
                    "id": voice_id
                },
                "output_format": {
                    "container": audio_params['container'],
                    "encoding": audio_params['encoding'],
                    "sample_rate": audio_params['sample_rate'],
                },
                "generation_config": {
                    "volume": voice_params['volume'],
                    "speed": voice_params['speed'],
                    "emotion": voice_params['emotion'],
                },
                "language": voice_params['language'],
                "add_timestamps": False,
                "add_phoneme_timestamps": False,
                "use_normalized_timestamps": True,
            }

            # Build headers
            headers = {
                "X-API-Key": self.api_key,
                "Cartesia-Version": self.api_version,
                "Content-Type": "application/json",
            }

            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Make API call
            url = f"{self.api_base.rstrip('/')}/tts/bytes"
            self.logger.debug(
                f"Calling Cartesia TTS: model={self.model_id}, voice={voice_id}, "
                f"container={audio_params['container']}, encoding={audio_params['encoding']}, "
                f"sample_rate={audio_params['sample_rate']}"
            )
            
            audio_bytes = self._http_post_bytes(url, headers, payload)

            if not audio_bytes:
                self.last_error = "Cartesia returned empty audio bytes"
                self.logger.error(self.last_error)
                return False

            # Write audio to file (in chunks for large files)
            chunk_size = 8192
            with open(output_path, "wb") as f:
                if len(audio_bytes) > chunk_size:
                    for i in range(0, len(audio_bytes), chunk_size):
                        f.write(audio_bytes[i:i + chunk_size])
                else:
                    f.write(audio_bytes)

            # Verify output
            if output_path.exists() and output_path.stat().st_size > 0:
                file_size = output_path.stat().st_size
                self.logger.debug(
                    f"Synthesis successful: {output_path} ({file_size/1024:.1f}KB)"
                )
                self.last_error = None  # Clear last error on success
                return True
            
            self.last_error = "Output file not created or empty after write"
            self.logger.error(self.last_error)
            return False
            
        except RuntimeError as e:
            # HTTP/Network errors already logged with details
            self.last_error = f"Cartesia synthesis failed: {e}"
            self.logger.error(f"❌ {self.last_error}")
            return False
        except Exception as e:
            # Unexpected errors - log with traceback
            import traceback
            self.last_error = f"Cartesia synthesis failed with unexpected error: {e}"
            self.logger.error(f"❌ {self.last_error}")
            self.logger.debug(traceback.format_exc())
            return False

    def synthesize_with_metadata(
        self,
        text: str,
        output_file: Path,
        generation_config: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize with comprehensive metadata information (compatible with enhanced system).
        Accepts optional GenerationConfig to control per-call model, voice, and audio params.
        
        Args:
            text: Text to synthesize
            output_file: Path to save the output audio file
            generation_config: Optional GenerationConfig providing model, voice_config, and audio_config
            
        Returns:
            Dictionary containing synthesis results and metadata
        """
        from speech_synth_engine.schemas.provider import VoiceConfig, AudioConfig
        from speech_synth_engine.schemas.generation import GenerateSpeechConfig

        # If a GenerationConfig is provided, use it; otherwise build a minimal one
        gen_cfg: GenerateSpeechConfig
        if generation_config is not None:
            gen_cfg = generation_config
            # Ensure voice_config exists
            try:
                if getattr(gen_cfg, 'voice_config', None) is None or getattr(gen_cfg.voice_config, 'voice_id', None) is None:
                    gen_cfg = GenerateSpeechConfig(
                        model=getattr(gen_cfg, 'model', self.model_id),
                        voice_config=VoiceConfig(voice_id=""),
                        audio_config=getattr(gen_cfg, 'audio_config', None)
                    )
                # Update provider's runtime model/sample_rate to reflect this call
                if getattr(gen_cfg, 'model', None):
                    self.model_id = gen_cfg.model
                if getattr(gen_cfg, 'audio_config', None) and getattr(gen_cfg.audio_config, 'sample_rate', None):
                    self.sample_rate = gen_cfg.audio_config.sample_rate
            except Exception:
                gen_cfg = GenerateSpeechConfig(
                    model=self.model_id,
                    voice_config=VoiceConfig(voice_id=""),
                    audio_config=AudioConfig(channel=1, sample_rate=self.sample_rate, container=self.default_container)
                )
        else:
            gen_cfg = GenerateSpeechConfig(
                model=self.model_id,
                voice_config=VoiceConfig(voice_id=""),
                audio_config=AudioConfig(channel=1, sample_rate=self.sample_rate, container=self.default_container)
            )

        # Resolve effective voice
        effective_voice = getattr(gen_cfg.voice_config, 'voice_id', None) if getattr(gen_cfg, 'voice_config', None) else None
        if not effective_voice:
            supported = self._get_supported_voices()
            effective_voice = supported[0] if supported else ""
            # Update gen_cfg with resolved voice
            try:
                if getattr(gen_cfg, 'voice_config', None):
                    gen_cfg.voice_config.voice_id = effective_voice
                else:
                    gen_cfg = GenerateSpeechConfig(
                        model=gen_cfg.model,
                        voice_config=VoiceConfig(voice_id=effective_voice),
                        audio_config=gen_cfg.audio_config
                    )
            except Exception:
                pass

        success = self.synthesize(text, output_file, generation_config=gen_cfg)

        # Build effective configs (reflect what was actually used)
        eff_voice_cfg = {
            "voice_id": effective_voice,
            "language": getattr(gen_cfg.voice_config, "language", None) if gen_cfg and getattr(gen_cfg, 'voice_config', None) else None,
            "speed": getattr(gen_cfg.voice_config, "speed", None) if gen_cfg and getattr(gen_cfg, 'voice_config', None) else None,
            "volume": getattr(gen_cfg.voice_config, "volume", None) if gen_cfg and getattr(gen_cfg, 'voice_config', None) else None,
            "emotion": getattr(gen_cfg.voice_config, "emotion", None) if gen_cfg and getattr(gen_cfg, 'voice_config', None) else None,
        }
        eff_audio_cfg = {
            "container": getattr(gen_cfg.audio_config, "container", None) if gen_cfg and getattr(gen_cfg, 'audio_config', None) else None,
            "encoding": getattr(gen_cfg.audio_config, "encoding", None) if gen_cfg and getattr(gen_cfg, 'audio_config', None) else None,
            "sample_rate": getattr(gen_cfg.audio_config, "sample_rate", None) if gen_cfg and getattr(gen_cfg, 'audio_config', None) else None,
            "channel": getattr(gen_cfg.audio_config, "channel", None) if gen_cfg and getattr(gen_cfg, 'audio_config', None) else None,
        }

        # Model should reflect what was passed in GenerationConfig if provided
        eff_model = getattr(gen_cfg, 'model', None) if gen_cfg else self.model_id

        error_detail = None if success else "Synthesis failed"

        from speech_synth_engine.schemas.schemas import SynthesisResult
        if success:
            return SynthesisResult(
                success=True,
                text=text,
                output_file=str(Path(output_file).absolute()),
                provider=self.name,
                model=eff_model,
                effective_voice_config=eff_voice_cfg,
                effective_audio_config=eff_audio_cfg
            )
        else:
            return SynthesisResult(
                success=False,
                text=text,
                output_file=None,
                provider=self.name,
                model=eff_model,
                effective_voice_config=eff_voice_cfg,
                effective_audio_config=eff_audio_cfg,
                error={"message": "Synthesis failed", "detail": error_detail}
            )