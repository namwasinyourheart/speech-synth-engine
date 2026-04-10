from pathlib import Path
import os
import wave
import logging
from google import genai
from google.genai import types
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Import the base provider and API key manager
from .base.provider import TTSProvider
from speech_synth_engine.schemas.provider import VoiceConfig, AudioConfig, ProviderConfig
from .api_keys import APIKeyManager

# Load environment variables
load_dotenv()

class GeminiTTSProvider(TTSProvider):
    """
    TTS provider using Google Gemini TTS.
    Updated to inherit from TTSProvider with full enhanced features.
    """

    def __init__(self, name: str = "gemini-tts", provider_config: Optional[ProviderConfig] = None):
        """
        GeminiTTSProvider chỉ sử dụng provider_config (chuẩn schema) để cấu hình.
        Không còn sử dụng self.config hay bất kỳ dict config nào khác, đồng bộ với CartesiaTTSProvider.
        """
        # Khởi tạo base với provider_config
        super().__init__(name, {"provider_config": provider_config} if provider_config else {})
        self.logger = logging.getLogger(f"TTSProvider.{self.name}")
        self.provider_config: Optional[ProviderConfig] = provider_config
        # Track last error for detailed error reporting
        self.last_error: Optional[str] = None
        # Lấy các thông tin cấu hình chính từ provider_config
        provider_cfg = self.provider_config
        self.default_model = self._get_supported_models()[0]  # Provider-level constant, not user-configurable
        self.default_voice_id = self._get_supported_voices()[0]  # Provider-level constant, not user-configurable
        self.default_sample_rate = 24000  # Provider-level constant, not user-configurable
        # use_vertex_ai: chỉ bật qua env USE_VERTEX_AI (có trong credentials.envs hoặc biến toàn cục)
        self.use_vertex_ai = False
        if provider_cfg and hasattr(provider_cfg, 'credentials') and provider_cfg.credentials:
            try:
                # Chỉ chấp nhận boolean: 'true' (không phân biệt hoa thường)
                def _is_true(val: str) -> bool:
                    return isinstance(val, str) and val.strip().lower() == 'true'
                # Kiểm tra trong danh sách envs được khai báo
                for env_name in getattr(provider_cfg.credentials, 'envs', []) or []:
                    if env_name.upper() == 'USE_VERTEX_AI':
                        val = os.getenv(env_name)
                        if _is_true(val):
                            self.use_vertex_ai = True
                            break
                # Nếu chưa bật, kiểm tra env toàn cục USE_VERTEX_AI
                if not self.use_vertex_ai:
                    val = os.getenv('USE_VERTEX_AI')
                    if _is_true(val):
                        self.use_vertex_ai = True
            except Exception:
                # Không cản trở khởi tạo nếu lỗi parse env
                pass
        # Single-key mode only from now on
        self.rotate_api_keys = False
        self.logger.debug("Gemini provider initialized using only provider_config (no self.config).")

        try:
            if self.use_vertex_ai:
                provider_cfg = getattr(self, 'provider_config', None)
                if not (provider_cfg and getattr(provider_cfg, 'credentials', None)):
                    raise ValueError("CredentialsConfig required for Vertex AI mode")

                from speech_synth_engine.utils import extract_vertex_ai_credentials, get_gemini_vertex_ai_client
                cred_cfg = provider_cfg.credentials
                credentials_path, project_id, location = extract_vertex_ai_credentials(cred_cfg)

                if not location:
                    location = 'us-central1'

                if not credentials_path or not project_id:
                    raise ValueError(
                        "Both 'credentials_path' and 'project_id' must be provided when using Vertex AI (from CredentialsConfig)"
                    )

                self.client = get_gemini_vertex_ai_client(credentials_path, project_id, location)
                self.logger.debug("Successfully initialized Gemini client with Vertex AI")

            else:
                # Single-key mode: resolve key via helper for concise logic
                provider_cfg = self.provider_config
                cred = provider_cfg.credentials if (provider_cfg and getattr(provider_cfg, 'credentials', None)) else None
                from speech_synth_engine.utils import resolve_api_key_from_credentials, get_gemini_api_key_client
                api_key = resolve_api_key_from_credentials(cred, env_fallback='GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("No API key provided. Set 'api_keys' in config or GEMINI_API_KEY in environment.")
                self.client = get_gemini_api_key_client(api_key)
                self.logger.debug("Successfully initialized Gemini client with API key")
                self.logger.debug(f"Using API key ending with ...{api_key[-4:]}")

                
        except ImportError as e:
            error_msg = "google-generativeai package is required. Install with: pip install google-generativeai"
            self.logger.error(error_msg)
            raise ImportError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize Gemini client: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _get_supported_models(self) -> List[str]:
        """Return all supported Gemini TTS model names."""
        return [
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-pro-preview-tts",
        ]

    def _get_supported_voices(self) -> List[str]:
        """Gemini TTS supports multiple multilingual voices"""
        return [
            "Achernar",
            "Achird",
            "Algenib",
            "Algieba",
            "Alnilam",
            "Aoede",
            "Autonoe",
            "Callirrhoe",
            "Charon",
            "Despina",
            "Enceladus",
            "Erinome",
            "Fenrir",
            "Gacrux",
            "Iapetus",
            "Kore",
            "Laomedeia",
            "Leda",
            "Orus",
            "Pulcherrima",
            "Puck",
            "Rasalgethi",
            "Sadachbia",
            "Sadaltager",
            "Schedar",
            "Sulafat",
            "Umbriel",
            "Vindemiatrix",
            "Zephyr",
            "Zubenelgenubi"
        ]

    @staticmethod
    def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
        """
        Save PCM bytes to WAV file.
        """
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

    def _synthesize_with_vertex_ai(self, text: str, voice: str, model: Optional[str] = None) -> bytes:
        """Helper method to handle Vertex AI synthesis"""
        try:
            effective_model = model or self.default_model
            self.logger.debug(f"Calling Gemini TTS API with model: {effective_model}, text: {text[:50]}...")
            response = self.client.models.generate_content(
                model=effective_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    ),
                ),
            )
            return response.candidates[0].content.parts[0].inline_data.data
        except Exception as e:
            self.logger.error(f"Vertex AI synthesis failed: {str(e)}")
            raise

    def _synthesize_with_api_key(self, text: str, voice: str, model: Optional[str] = None) -> bytes:
        """Helper method to handle API key based synthesis"""
        try:
            effective_model = model or self.default_model
            self.logger.debug(f"Using model: {effective_model}, voice: {voice}")
            self.logger.debug(f"Calling Gemini TTS API for text: {text[:50]}...")
            response = self.client.models.generate_content(
                model=effective_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    ),
                ),
            )
            pcm = response.candidates[0].content.parts[0].inline_data.data
            if pcm is None:
                raise RuntimeError("Gemini returned no audio data (got None). Try a shorter or clearer prompt.")
            return pcm
        except Exception as e:
            self.logger.error(f"API Key synthesis failed: {str(e)}")
            raise

    def synthesize(
        self,
        text: str,
        output_file: Path,
        generation_config: Optional[Any] = None,
        max_retries: int = 3,
    ) -> bool:
        """
        Synthesize audio from text and save to output_file.
        
        Args:
            text: Text to synthesize
            output_file: Path to save the output audio file
            generation_config: Optional GenerateSpeechConfig providing model, voice_config, and audio_config
            max_retries: Not used (single-attempt only)
            
        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        # Clear any previous error
        self.last_error = None
        
        # If a GenerateSpeechConfig is provided, derive configs from it
        # Resolve configs from GenerateSpeechConfig (if provided)
        voice_cfg = None
        audio_cfg = None
        effective_model = self.default_model
        if generation_config is not None:
            try:
                # Validate and set model
                model = getattr(generation_config, 'model', None)
                if model:
                    if model not in self._get_supported_models():
                        self.last_error = f"Model '{model}' is not supported. Available models: {self._get_supported_models()}"
                        self.logger.error(self.last_error)
                        return False
                    effective_model = model
                voice_cfg = getattr(generation_config, 'voice_config', None)
                audio_cfg = getattr(generation_config, 'audio_config', None)
                # Determine sample rate for this synthesis
                sample_rate = getattr(audio_cfg, 'sample_rate', None) or self.default_sample_rate
            except Exception:
                pass

        # Validate text before synthesizing
        if not self.validate_text(text):
            self.last_error = f"Invalid text: {text[:50]}..."
            self.logger.error(self.last_error)
            return False

        # Determine effective voice (required)
        if not voice_cfg or not getattr(voice_cfg, 'voice_id', None):
            self.last_error = "voice_config with voice_id is required"
            self.logger.error(self.last_error)
            return False
        effective_voice = voice_cfg.voice_id

        # Validate voice
        if effective_voice not in self.supported_voices:
            self.last_error = f"Voice '{effective_voice}' is not supported. Available voices: {self.supported_voices}"
            self.logger.error(self.last_error)
            return False

        # Ensure output_file is a Path object and create parent directories
        output_file = Path(output_file) if not isinstance(output_file, Path) else output_file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Resolve audio output parameters
        channels = (audio_cfg.channel if (audio_cfg and getattr(audio_cfg, 'channel', None) is not None) else 1)
        sample_rate = (audio_cfg.sample_rate if (audio_cfg and getattr(audio_cfg, 'sample_rate', None) is not None) else self.default_sample_rate)
        sample_width = 2  # fixed as requested; keep default 2

        # For Vertex AI, we don't need API key rotation
        if self.use_vertex_ai:
            try:
                pcm_data = self._synthesize_with_vertex_ai(text, effective_voice, effective_model)
                self.save_wave(str(output_file), pcm_data, channels=channels, rate=sample_rate, sample_width=sample_width)
                self.logger.debug(f"Synthesis successful: {output_file}")
                return True
            except Exception as e:
                self.last_error = f"Synthesis failed: {e}"
                self.logger.error(self.last_error)
                return False
        
        # For API key based authentication (single attempt, no rotation)
        try:
            pcm_data = self._synthesize_with_api_key(text, effective_voice, effective_model)
            if pcm_data is None:
                self.last_error = "Received no audio data from Gemini (None)."
                self.logger.error(self.last_error)
                return False
            self.logger.debug(f"Received {len(pcm_data)} bytes of PCM audio")
            self.save_wave(str(output_file), pcm_data, channels=channels, rate=sample_rate, sample_width=sample_width)
            self.logger.debug(f"Synthesis successful: {output_file}")
            self.last_error = None  # Clear last error on success
            return True
        except Exception as e:
            self.last_error = f"Synthesis failed: {e}"
            self.logger.error(self.last_error)
            return False

    def clone(self, text: str, reference_audio: Path, output_file: Path) -> bool:
        """
        Gemini TTS provider does not support voice cloning.
        
        Args:
            text: Text to synthesize
            reference_audio: Reference audio for voice cloning (not used)
            output_file: Path to save the output audio file
            
        Returns:
            bool: Always returns False as voice cloning is not supported
        """
        self.logger.warning(" Gemini TTS provider does not support voice cloning")
        return False

    def synthesize_with_metadata(
        self,
        text: str,
        output_file: Path,
        generation_config: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize with comprehensive metadata information (compatible with enhanced system).
        Accepts optional GenerateSpeechConfig to control per-call model, voice, and audio params.
        """
        from speech_synth_engine.schemas.provider import VoiceConfig, AudioConfig
        from speech_synth_engine.schemas.generation import GenerateSpeechConfig

        # If a GenerationConfig is provided, use it; otherwise build a minimal one.
        gen_cfg: GenerateSpeechConfig
        if generation_config is not None:
            # Start from provided config
            gen_cfg = generation_config
            # Ensure voice is applied from the method arg
            try:
                if getattr(gen_cfg, 'voice_config', None) is None or getattr(gen_cfg.voice_config, 'voice_id', None) is None:
                    gen_cfg = GenerateSpeechConfig(
                        model=getattr(gen_cfg, 'model', self.default_model),
                        voice_config=VoiceConfig(voice_id=getattr(gen_cfg, 'voice', None) or self.default_voice_id),
                        audio_config=getattr(gen_cfg, 'audio_config', None)
                    )
                # else: keep provided voice_id as-is
                # Do not mutate provider default sample rate here; per-request sample rate will be respected via gen_cfg
                # if getattr(gen_cfg, 'audio_config', None) and getattr(gen_cfg.audio_config, 'sample_rate', None):
                #     pass
            except Exception:
                # Fallback to minimal config if any issue
                gen_cfg = GenerateSpeechConfig(
                    model=self.default_model,
                    voice_config=VoiceConfig(voice_id=self.default_voice_id),
                    audio_config=AudioConfig(channel=1, sample_rate=self.default_sample_rate)
                )
        else:
            gen_cfg = GenerateSpeechConfig(
                model=self.default_model,
                voice_config=VoiceConfig(voice_id=self.default_voice_id),
                audio_config=AudioConfig(channel=1, sample_rate=self.default_sample_rate)
            )

        # Validate model
        effective_model = getattr(gen_cfg, 'model', self.default_model)
        if effective_model not in self._get_supported_models():
            error_msg = f"Model '{effective_model}' is not supported. Available models: {self._get_supported_models()}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": text,
                "output_file": None,
                "provider": self.name,
                "error": {"message": "Model validation failed", "detail": error_msg},
            }

        # Resolve effective voice
        effective_voice = getattr(gen_cfg, 'voice_config', None)
        effective_voice = getattr(effective_voice, 'voice_id', None)
        if not effective_voice:
            effective_voice = self.default_voice_id

        # Validate voice
        if effective_voice not in self.supported_voices:
            error_msg = f"Voice '{effective_voice}' is not supported. Available voices: {self.supported_voices}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": text,
                "output_file": None,
                "provider": self.name,
                "error": {"message": "Voice validation failed", "detail": error_msg},
            }

        # Make sure voice_config in gen_cfg reflects the resolved voice
        try:
            if getattr(gen_cfg, 'voice_config', None) is None:
                gen_cfg = GenerateSpeechConfig(
                    model=getattr(gen_cfg, 'model', self.default_model),
                    voice_config=VoiceConfig(voice_id=effective_voice),
                    audio_config=gen_cfg.audio_config
                )
            else:
                gen_cfg.voice_config.voice_id = effective_voice
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

        # Model should reflect what was passed in GenerateSpeechConfig if provided
        eff_model = getattr(gen_cfg, 'model', None) if gen_cfg else self.default_model

        # We don't currently propagate detailed errors from synthesize(); keep placeholder
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
                error={'message': 'Synthesis failed', 'detail': error_detail}
            )

