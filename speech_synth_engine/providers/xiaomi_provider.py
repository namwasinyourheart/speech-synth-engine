# Xiaomi TTS Provider with Voice Cloning Support
# Supports OmniVoice API for voice cloning from reference audio
#
# Voice Cloning API:
# curl --location 'https://rxcvyunvtyun--k2-fsa--omnivoice-serve.modal.run/run/k2-fsa/OmniVoice/clone' \
# --header 'accept: audio/wav' \
# --form 'text="Em yêu anh nhiều lắm";type=application/json' \
# --form 'language="vi";type=application/json' \
# --form 'ref_audio=@"/path/to/reference.mp3"' \
# --form 'ref_text="null";type=application/json'

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
from speech_synth_engine.schemas.provider import PrebuiltVoiceConfig, ReplicatedVoiceConfig, AudioConfig, ProviderConfig
from .utils import resolve_api_key, extract_voice_params, extract_audio_params, validate_enum_value
import mimetypes

# Load environment variables
load_dotenv()


class XiaomiTTSProvider(TTSProvider):
    """
    TTS provider using Xiaomi OmniVoice API.
    
    Supports voice cloning from reference audio using multipart/form-data.
    """
    
    # Provider defaults
    DEFAULT_CLONE_API_BASE = "https://rxcvyunvtyun--k2-fsa--omnivoice-serve.modal.run"
    DEFAULT_CLONE_ENDPOINT = "/run/k2-fsa/OmniVoice/clone"
    # DEFAULT_STT_API_BASE = "https://ai.vnpost.vn/voiceai/core/stt/v1"
    # DEFAULT_STT_ENDPOINT = "/transcript"
    DEFAULT_STT_API_BASE = "http://0.0.0.0:13081/asr/v1/"
    DEFAULT_STT_ENDPOINT = "file"
    DEFAULT_LANGUAGE = "vi"
    
    # API limits
    MAX_TEXT_LENGTH = 5000  # characters
    
    # Cache for transcribed reference audio to avoid re-transcribing
    _transcription_cache = {}

    def __init__(self, name: str = "xiaomi", provider_config: Optional[ProviderConfig] = None):
        super().__init__(name, {"provider_config": provider_config} if provider_config else {})

        self.logger = logging.getLogger(f"TTSProvider.{self.name}")
        # Remove duplicate handler setup - let parent class or root logger handle it
        # This prevents duplicate log messages

        # API configuration
        self.clone_api_base = self.DEFAULT_CLONE_API_BASE
        self.clone_endpoint = self.DEFAULT_CLONE_ENDPOINT
        self.stt_api_base = self.DEFAULT_STT_API_BASE
        self.stt_endpoint = self.DEFAULT_STT_ENDPOINT
        self.language = self.DEFAULT_LANGUAGE

        # Track last error for detailed error reporting
        self.last_error: Optional[str] = None

        self.logger.debug("Initialized Xiaomi OmniVoice provider")

    def _get_supported_voices(self) -> List[str]:
        """Xiaomi uses voice cloning, no predefined voice IDs."""
        return []

    def transcribe_audio(self, audio_file_path: str, model_name: str = "vnp/stt_a1", enhance_speech: bool = True, postprocess_text: bool = True) -> str:
        """
        Transcribe audio file using VNPost STT API.
        
        Args:
            audio_file_path: Path to audio file
            model_name: STT model to use (default: vnp/stt_a1)
            enhance_speech: Whether to enhance speech (default: True)
            postprocess_text: Whether to postprocess text (default: True)
            
        Returns:
            Transcribed text or empty string on error
        """
        try:
            audio_file = Path(audio_file_path)
            if not audio_file.exists():
                self.logger.error(f"Audio file not found: {audio_file_path}")
                return ""

            # Read audio file
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # Detect content type
            content_type, _ = mimetypes.guess_type(str(audio_file))
            if not content_type:
                content_type = 'audio/mpeg'  # default

            # Prepare multipart form data
            fields = {
                'model_name': model_name,
                'enhance_speech': enhance_speech,  # Pass boolean directly
                'postprocess_text': postprocess_text,  # Pass boolean directly
            }
            
            files = {
                'audio_file': (audio_file.name, audio_data, content_type)
            }

            # Make API call
            url = f"{self.stt_api_base.rstrip('')}{self.stt_endpoint}"
            
            response_bytes = self._http_post_multipart(url, fields, files)
            
            # Parse JSON response
            response_text = response_bytes.decode('utf-8')
            response_data = json.loads(response_text)
            
            # Extract transcript
            transcript = response_data.get('text', '')
            if not transcript:
                self.logger.warning(f"⚠️ No transcript returned from STT API")
                return ""
            
            return transcript
            
        except RuntimeError as e:
            self.logger.error(f"❌ STT failed: {e}")
            return ""
        except Exception as e:
            import traceback
            self.logger.error(f"❌ STT failed with unexpected error: {e}")
            self.logger.debug(traceback.format_exc())
            return ""

    @staticmethod
    def _http_post_multipart(url: str, fields: Dict[str, Any], files: Dict[str, tuple]) -> bytes:
        """
        Perform HTTP POST with multipart/form-data using stdlib.
        
        Args:
            url: API endpoint URL
            fields: Form fields (text, language, ref_text)
            files: Files to upload {field_name: (filename, file_data, content_type)}
            
        Returns:
            Raw response bytes
            
        Raises:
            RuntimeError: On HTTP or network errors
        """
        import uuid
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
        
        # Build multipart body
        body_parts = []
        
        # Add text fields
        for name, value in fields.items():
            body_parts.append(f'--{boundary}'.encode())
            body_parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
            body_parts.append(f'Content-Type: application/json'.encode())
            body_parts.append(b'')
            body_parts.append(json.dumps(value).encode('utf-8'))
        
        # Add file fields
        for field_name, (filename, file_data, content_type) in files.items():
            body_parts.append(f'--{boundary}'.encode())
            body_parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode()
            )
            body_parts.append(f'Content-Type: {content_type}'.encode())
            body_parts.append(b'')
            body_parts.append(file_data)
        
        # Final boundary
        body_parts.append(f'--{boundary}--'.encode())
        body_parts.append(b'')
        
        body = b'\r\n'.join(body_parts)
        
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Accept': 'audio/wav',
        }
        
        req = Request(url, data=body, headers=headers, method='POST')
        
        try:
            with urlopen(req) as resp:
                return resp.read()
        except HTTPError as e:
            body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
            body_preview = body[:500] + '...' if len(body) > 500 else body
            raise RuntimeError(f"HTTP {e.code}: {body_preview}")
        except URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")

    def clone(
        self,
        text: str,
        output_file: Path,
        voice_cloning_config: Optional[Any] = None,
    ) -> bool:
        """
        Clone voice from reference audio and synthesize text.
        
        Args:
            text: Text to synthesize
            output_file: Path to save the output audio file
            voice_cloning_config: Optional VoiceCloningConfig with ReplicatedVoiceConfig
            
        Returns:
            True if cloning succeeded, False otherwise
        """
        # Clear any previous error
        self.last_error = None
        
        try:
            if not self.validate_text(text):
                self.last_error = "Invalid text provided for cloning"
                self.logger.error(self.last_error)
                return False

            # Validate text length
            if len(text) > self.MAX_TEXT_LENGTH:
                self.logger.warning(
                    f"Text length ({len(text)}) exceeds recommended limit ({self.MAX_TEXT_LENGTH})"
                )

            # Extract voice_config from voice_cloning_config
            voice_config = None
            if voice_cloning_config is not None:
                voice_config = getattr(voice_cloning_config, 'voice_config', None)
            
            if not voice_config or not isinstance(voice_config, ReplicatedVoiceConfig):
                self.last_error = "ReplicatedVoiceConfig is required for voice cloning"
                self.logger.error(self.last_error)
                return False

            # Get reference audio path
            ref_audio_path = getattr(voice_config, 'reference_audio', None)
            if not ref_audio_path:
                self.last_error = "reference_audio is required in ReplicatedVoiceConfig"
                self.logger.error(self.last_error)
                return False
            
            ref_audio_file = Path(ref_audio_path)
            if not ref_audio_file.exists():
                self.last_error = f"Reference audio file not found: {ref_audio_path}"
                self.logger.error(self.last_error)
                return False

            # Get optional parameters
            ref_text = getattr(voice_config, 'reference_text', None)
            language = getattr(voice_config, 'language', None) or self.language

            # Auto-transcribe if ref_text is not provided
            if not ref_text:
                self.logger.info("No reference_text provided, attempting auto-transcription...")
                transcript = self.transcribe_audio(str(ref_audio_path))
                if transcript:
                    ref_text = transcript
                    self.logger.info(f"Auto-transcribed reference text: {ref_text[:50]}...")
                    # Update the voice config with the transcribed text for metadata
                    if hasattr(voice_config, 'reference_text'):
                        voice_config.reference_text = ref_text
                else:
                    ref_text = "null"  # fallback
                    self.logger.warning("⚠️ Transcription failed, using null fallback")
            else:
                ref_text = str(ref_text)  # Ensure it's a string

            # Read reference audio file for cloning
            with open(ref_audio_file, 'rb') as f:
                ref_audio_data = f.read()
            
            # Detect content type
            content_type, _ = mimetypes.guess_type(str(ref_audio_file))
            if not content_type:
                content_type = 'audio/mpeg'  # default

            # Prepare multipart form data
            fields = {
                'text': text,
                'language': language,
                'ref_text': ref_text,
            }
            
            files = {
                'ref_audio': (ref_audio_file.name, ref_audio_data, content_type)
            }

            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Make API call
            url = f"{self.clone_api_base.rstrip('')}{self.clone_endpoint}"
            self.logger.debug(
                f"Cloning voice: '{text[:60]}{'...' if len(text) > 60 else ''}' (ref: {ref_audio_file.name})"
            )
            
            audio_bytes = self._http_post_multipart(url, fields, files)

            if not audio_bytes:
                self.last_error = "Xiaomi OmniVoice returned empty audio bytes"
                self.logger.error(self.last_error)
                return False

            # Write audio to file
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            # Verify output
            if output_path.exists() and output_path.stat().st_size > 0:
                file_size = output_path.stat().st_size
                self.logger.debug(
                    f"Cloned successfully ({file_size/1024:.1f}KB)"
                )
                self.last_error = None  # Clear last error on success
                return True
            
            self.last_error = "Output file not created or empty after write"
            self.logger.error(self.last_error)
            return False
            
        except RuntimeError as e:
            self.last_error = f"Xiaomi voice cloning failed: {e}"
            self.logger.error(f"❌ {self.last_error}")
            return False
        except Exception as e:
            import traceback
            self.last_error = f"Xiaomi voice cloning failed with unexpected error: {e}"
            self.logger.error(f"❌ {self.last_error}")
            self.logger.debug(traceback.format_exc())
            return False

    def clone_with_metadata(
        self,
        text: str,
        output_file: Path,
        voice_cloning_config: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Clone voice with comprehensive metadata information.
        
        Args:
            text: Text to synthesize
            output_file: Path to save the output audio file
            voice_cloning_config: Optional VoiceCloningConfig with ReplicatedVoiceConfig
            
        Returns:
            Dictionary containing cloning results and metadata
        """
        from speech_synth_engine.schemas.provider import ReplicatedVoiceConfig
        from speech_synth_engine.schemas.schemas import SynthesisResult

        success = self.clone(text, output_file, voice_cloning_config=voice_cloning_config)

        # Extract voice config for metadata
        voice_config = None
        if voice_cloning_config:
            voice_config = getattr(voice_cloning_config, 'voice_config', None)
        
        eff_voice_cfg = {}
        if voice_config and isinstance(voice_config, ReplicatedVoiceConfig):
            eff_voice_cfg = {
                "reference_audio": getattr(voice_config, "reference_audio", None),
                "reference_text": getattr(voice_config, "reference_text", None),
                "enhance_speech": getattr(voice_config, "enhance_speech", False),
                "language": getattr(voice_config, "language", None),
            }

        error_detail = None if success else "Voice cloning failed"

        if success:
            return SynthesisResult(
                success=True,
                text=text,
                output_file=str(Path(output_file).absolute()),
                provider=self.name,
                model="OmniVoice",
                effective_voice_config=eff_voice_cfg
            )
        else:
            return SynthesisResult(
                success=False,
                text=text,
                output_file=None,
                provider=self.name,
                model="OmniVoice",
                effective_voice_config=eff_voice_cfg,
                error={'message': 'Voice cloning failed', 'detail': error_detail}
            )
    
    def synthesize(self, text: str, output_file: Path, generation_config: Optional[Any] = None) -> bool:
        """Not supported - use clone() instead."""
        self.last_error = "XiaomiTTSProvider only supports voice cloning via clone() method"
        self.logger.error(self.last_error)
        return False
    
    def synthesize_with_metadata(self, text: str, output_file: Path, generation_config: Optional[Any] = None) -> Dict[str, Any]:
        """Not supported - use clone_with_metadata() instead."""
        return {
            "success": False,
            "text": text,
            "output_file": None,
            "provider": self.name,
            "error": {'message': 'XiaomiTTSProvider only supports voice cloning via clone_with_metadata() method'}
        }