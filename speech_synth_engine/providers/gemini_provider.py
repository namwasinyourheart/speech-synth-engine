from pathlib import Path
import os
import wave
import logging
from google import genai
from google.genai import types
from typing import Dict, List, Any
from dotenv import load_dotenv

# Import the base provider and API key manager
from .base.provider import TTSProvider
from .api_keys import APIKeyManager

# Load environment variables
load_dotenv()

class GeminiTTSProvider(TTSProvider):
    """
    TTS provider using Google Gemini TTS.
    Updated to inherit from TTSProvider with full enhanced features.
    """

    def __init__(self, name: str = "gemini-tts", config: Dict[str, Any] = None):
        # Initialize with empty config first to set up base attributes
        super().__init__(name, config or {})
        
        # Set up logger
        self.logger = logging.getLogger(f"TTSProvider.{self.name}")
        if not self.logger.handlers:  # Avoid adding multiple handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Update config with provided values
        self.config = config or {}

        # print(f"Config: {self.config}")
        
        # Set default configuration
        self.model = self.config.get('model', 'gemini-2.5-flash-preview-tts')
        self.sample_rate = self.config.get('sample_rate', 24000)
        self.use_vertex_ai = self.config.get('use_vertex_ai', False)
        self.rotate_api_keys = self.config.get('rotate_api_keys', False)

        # Initialize API key manager
        self.key_manager = APIKeyManager(
            provider_name="Gemini",
            env_var_prefix="GEMINI_API_KEY"
        )
        
        try:
            if self.use_vertex_ai:
                # Initialize with Vertex AI credentials
                from google.oauth2 import service_account
                
                credentials_path = self.config.get('credentials_path')
                project_id = self.config.get('project_id')
                location = self.config.get('location', 'us-central1')
                
                if not credentials_path or not project_id:
                    raise ValueError("Both 'credentials_path' and 'project_id' must be provided when using Vertex AI")
                
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                
                self.client = genai.Client(
                    credentials=credentials,
                    vertexai=True,
                    project=project_id,
                    location=location
                )
                self.logger.info("Successfully initialized Gemini client with Vertex AI")
                
            else:
                api_keys = self.config.get('api_keys')
                # print(f"API keys: {api_keys}")
                if isinstance(api_keys, str):
                    api_keys = [key.strip() for key in api_keys.split(',') if key.strip()]

                if self.rotate_api_keys:
                    # Initialize with API key
                    # Try to get API keys from config first, then fall back to environment variables
                    # api_keys = self.config.get('api_keys')
                    # if isinstance(api_keys, str):
                    #     api_keys = [key.strip() for key in api_keys.split(',') if key.strip()]
                
                    if api_keys:
                        # If API keys are provided in config, set them as environment variables
                        for i, key in enumerate(api_keys, 1):
                            os.environ[f'GEMINI_API_KEY_{i}'] = key
                
                    # # Initialize API key manager
                    # self.key_manager = APIKeyManager(
                    #     provider_name="Gemini",
                    #     env_var_prefix="GEMINI_API_KEY"
                    # )
                    
                    # Initialize Gemini client with the current key
                    self.client = genai.Client(api_key=self.key_manager.get_current_key())
                    self.logger.info("Successfully initialized Gemini client with API key")
                    self.logger.info(f"Using API key ending with ...{self.key_manager.get_current_key()[-4:]}")

                else:
                    if len(api_keys) > 1:
                        self.logger.info("Multiple API keys provided. Using the first one.")
                    
                    self.client = genai.Client(api_key=api_keys[0])
                    self.logger.info("Successfully initialized Gemini client with API key")
                    self.logger.info(f"Using API key ending with ...{api_keys[0][-4:]}")

                
        except ImportError as e:
            error_msg = "google-generativeai package is required. Install with: pip install google-generativeai"
            self.logger.error(error_msg)
            raise ImportError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize Gemini client: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _get_supported_voices(self) -> List[str]:
        """Gemini TTS supports multiple multilingual voices"""

        supported_voices = [
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
        return supported_voices

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

    def _synthesize_with_vertex_ai(self, text: str, voice: str) -> bytes:
        """Helper method to handle Vertex AI synthesis"""
        try:
            self.logger.info(f"🔄 [Vertex AI] Calling Gemini TTS API for text: {text[:50]}...")
            response = self.client.models.generate_content(
                model=self.model,
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

    def _synthesize_with_api_key(self, text: str, voice: str) -> bytes:
        """Helper method to handle API key based synthesis"""
        self.logger.info(f"🔧 [API Key] Using model: {self.model}, voice: {voice}, "
                       f"API key: ...{self.key_manager.get_current_key()[-4:]}")
        
        try:
            self.logger.info(f"🔄 [API Key] Calling Gemini TTS API for text: {text[:50]}...")
            response = self.client.models.generate_content(
                model=self.model,
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
            self.logger.error(f"API Key synthesis failed: {str(e)}")
            raise

    def synthesize(self, text: str, voice: str, output_file: Path, max_retries: int = 3) -> bool:
        """
        Enhanced synthesize with validation, error handling, and API key rotation.
        
        Args:
            text: Text to synthesize
            voice: Voice to use (must be in supported_voices)
            output_file: Path to save the output audio file
            max_retries: Maximum number of retries (only used with API key)
            
        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        import time
        retry_count = 0
        last_error = None
        
        # Validate text before synthesizing
        if not self.validate_text(text):
            self.logger.error(f"Invalid text: {text[:50]}...")
            return False

        # Validate voice
        if voice not in self.supported_voices:
            self.logger.error(f"Voice '{voice}' is not supported. Available voices: {self.supported_voices}")
            return False

        # Ensure output_file is a Path object and create parent directories
        output_file = Path(output_file) if not isinstance(output_file, Path) else output_file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # For Vertex AI, we don't need API key rotation
        if self.use_vertex_ai:
            try:
                pcm_data = self._synthesize_with_vertex_ai(text, voice)
                self.save_wave(str(output_file), pcm_data)
                self.logger.info(f"✅ Synthesis successful: {output_file}")
                return True
            except Exception as e:
                self.logger.error(f"Vertex AI synthesis failed: {str(e)}")
                return False
        
        # For API key based authentication with retry logic
        while retry_count <= max_retries:
            try:
                pcm_data = self._synthesize_with_api_key(text, voice)
                self.save_wave(str(output_file), pcm_data)
                self.logger.info(f"✅ Synthesis successful: {output_file}")
                return True
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                self.logger.warning(f"Attempt {retry_count}/{max_retries} failed: {last_error}")
                
                # Handle API key rotation for rate limits and quota errors
                if any(error_msg in str(e).lower() for error_msg in ["quota", "rate limit", "rate_limit", "429"]):
                    current_key = self.key_manager.get_current_key()
                    self.logger.warning(f"🔴 Marking current API key as exhausted due to error: {last_error}")
                    self.key_manager.mark_key_exhausted(current_key)
                
                if retry_count <= max_retries:
                    # Try with the next API key
                    next_key = self.key_manager.get_next_key()
                    if next_key:
                        self.client = genai.Client(api_key=next_key)
                        self.logger.info(f"🔄 Rotating to next API key: ...{next_key[-4:]}")
                        # Exponential backoff before retry
                        backoff_time = 2 ** retry_count
                        self.logger.info(f"⏳ Waiting {backoff_time} seconds before retry...")
                        time.sleep(backoff_time)
                    else:
                        self.logger.error("❌ No more API keys available")
                        break
                
        self.logger.error(f"Failed after {retry_count} attempts. Last error: {last_error}")
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
        self.logger.warning("❌ Gemini TTS provider does not support voice cloning")
        return False

    def synthesize_with_metadata(self, text: str, voice: str, output_file: Path) -> Dict[str, Any]:
        """
        Synthesize with comprehensive metadata information (compatible with enhanced system).
        """
        success = self.synthesize(text, voice, output_file)

        return {
            'success': success,
            'text': text,
            'voice': voice,
            'output_file': str(output_file),
            'provider': self.name,
            'sample_rate': self.sample_rate,
            'model': self.model,
            'estimated_duration': self.estimate_duration(text),
            'error': None if success else "Synthesis failed",
            'file_info': self.get_file_info(output_file) if success else {}
        }

# config = {
#     'use_vertex_ai': True,
#     'credentials_path': '/path/to/your/credentials.json',
#     'project_id': 'your-project-id',
#     'location': 'us-central1',  # Optional, defaults to us-central1
#     'model': 'gemini-2.5-flash-preview-tts',
#     'sample_rate': 24000
# }

# provider = GeminiTTSProvider('gemini-vertex', config)


# config = {
#     'use_vertex_ai': False,  # Default is False
#     'api_keys': ['your-api-key-1', 'your-api-key-2'],  # Or use environment variables
#     'model': 'gemini-2.5-flash-preview-tts',
#     'sample_rate': 24000
# }

# provider = GeminiTTSProvider('gemini-api', config)