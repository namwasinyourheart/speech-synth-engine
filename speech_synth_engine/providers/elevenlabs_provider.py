import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import the base provider
from .base.provider import TTSProvider
from .api_keys import APIKeyManager

# Load environment variables
load_dotenv()

class ElevenLabsProvider(TTSProvider):
    """
    TTS provider using ElevenLabs API.
    Requires ELEVENLABS_API_KEY environment variable to be set.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        # Initialize with empty config first to set up base attributes
        # We'll set up the logger and client after base initialization
        super().__init__(name, config or {})
        
        # Now set up our logger
        import logging
        self.logger = logging.getLogger(f"TTSProvider.{self.name}")
        if not self.logger.handlers:  # Avoid adding multiple handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Update config with provided values
        self.config = config or {}
        
        # Set default configuration
        self.model_id = self.config.get('model_id', self.config.get('model', 'eleven_v3'))
        self.default_voice_id = self.config.get('default_voice_id', 'pNInz6obpgDQGcFmaJgB')
        
        # Initialize API key manager
        self.key_manager = APIKeyManager(
            provider_name="ElevenLabs",
            env_var_prefix="ELEVENLABS_API_KEY"
        )
        
        # Log the model being used
        self.logger.info(f"Using model: {self.model_id}")
        
        # Initialize API key manager
        try:
            # Try to get API keys from config first, then fall back to environment variables
            api_keys = self.config.get('api_keys')
            if isinstance(api_keys, str):
                api_keys = [key.strip() for key in api_keys.split(',') if key.strip()]
            
            if api_keys:
                # If API keys are provided in config, set them as environment variables
                for i, key in enumerate(api_keys, 1):
                    os.environ[f'ELEVENLABS_API_KEY_{i}'] = key
            
            # # Initialize API key manager
            # self.key_manager = APIKeyManager(
            #     provider_name="ElevenLabs",
            #     env_var_prefix="ELEVENLABS_API_KEY"
            # )
            
            # Initialize ElevenLabs client with the first key
            from elevenlabs.client import ElevenLabs
            self.client = ElevenLabs(api_key=self.key_manager.get_current_key())
            self.logger.info("Successfully initialized ElevenLabs client")
            self.logger.info(f"Using API key ending with ...{self.key_manager.get_current_key()[-4:]}")
            
            # Now that client is initialized, update supported_voices
            self.supported_voices = self._get_supported_voices()
            
        except ImportError as e:
            error_msg = "elevenlabs package is required. Install with: pip install elevenlabs"
            self.logger.error(error_msg)
            raise ImportError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize ElevenLabs client: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        
        # Cache for available voices
        self._available_voices = None

    def _get_supported_voices(self) -> List[str]:
        """Get list of available voice IDs from ElevenLabs"""
        # Default voices to use if we can't fetch from the API
        default_voices = [
            'pNInz6obpgDQGcFmaJgB',  # Rachel
            # 'MF3mGyEYCl7XYWbV9V6O',  # Domi
            # 'D38z5RcWu1voky8WS1ja',  # Bella
            # 'XrExE9yKIg1WjnnlVkGX',  # Antoni
            # 'VR6AewLTigWG4xSOukaG',  # Elli
        ]
        
        # If we've already fetched voices, return them
        if hasattr(self, '_available_voices') and self._available_voices is not None:
            return self._available_voices
            
        # If client isn't initialized yet, return default voices
        if not hasattr(self, 'client') or self.client is None:
            if hasattr(self, 'logger'):
                self.logger.warning("Client not initialized, using default voices")
            return default_voices
            
        try:
            # Try to fetch voices from the API
            # response = self.client.voices.get_all()
            response = self.client.voices.search()

            # print("response.voices:", response.voices)
            
            # Check if the response has the expected structure
            if hasattr(response, 'voices') and isinstance(response.voices, list):
                self._available_voices = [voice.voice_id for voice in response.voices]
                if hasattr(self, 'logger'):
                    self.logger.info(f"Successfully fetched {len(self._available_voices)} voices from API")
                return self._available_voices
            else:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"Unexpected response format from ElevenLabs API: {response}")
                return default_voices
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error fetching voices from ElevenLabs API: {e}")
                self.logger.info("Using default voices")
            return default_voices

    def _make_api_call(self, text: str, voice_id: str, output_file: Path, max_retries: int = 3) -> bool:
        """
        Internal method to make the API call with retry logic.
        
        Args:
            text: The text to convert to speech
            voice_id: Voice ID to use
            output_file: Path to save the output audio file
            max_retries: Maximum number of retries with different API keys
            
        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        from elevenlabs.client import ElevenLabs
        
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # Make the API call with the current key
                self.logger.info(f"🔧 Using model_id: {self.model_id}, voice_id: {voice_id}, "
                               f"API key: ...{self.key_manager.get_current_key()[-4:]}")
                
                response = self.client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id=self.model_id,
                    language_code="vi"
                )
                
                # Save the audio to file
                with open(output_file, 'wb') as f:
                    for chunk in response:
                        if chunk:
                            f.write(chunk)
                
                # Verify the file was created
                if output_file.exists() and output_file.stat().st_size > 0:
                    return True
                else:
                    raise RuntimeError("Output file was not created or is empty")
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"API call failed: {e}")
                
                # Check if this is a quota exceeded error
                if self.key_manager.is_quota_exceeded_error(e):
                    self.logger.warning("Quota exceeded for current API key, rotating...")
                    self.key_manager.mark_key_exhausted(self.key_manager.get_current_key())
                    
                    # Get a new key and update the client
                    new_key = self.key_manager.rotate_key()
                    if new_key is None:
                        self.logger.error("No more API keys available")
                        break
                        
                    # Update the client with the new key
                    self.client = ElevenLabs(api_key=new_key)
                    self.logger.info(f"Rotated to new API key ending with ...{new_key[-4:]}")
                    retry_count += 1
                else:
                    # For other errors, don't retry with a different key
                    break
        
        self.logger.error(f"Failed after {retry_count} retries. Last error: {last_error}")
        return False

    def synthesize(self, text: str, voice: str = None, output_file: Path = None) -> bool:
        """
        Convert text to speech using ElevenLabs API with automatic key rotation.
        
        Args:
            text: The text to convert to speech
            voice: Voice ID to use (defaults to the one in config or default_voice_id)
            output_file: Path to save the output audio file
            
        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        try:
            # Validate text
            if not self.validate_text(text):
                self.logger.error(f"Invalid text: {text[:50]}...")
                return False
            
            # Use provided voice or default
            voice_id = voice or self.default_voice_id
            
            # If output_file is not provided, create a temporary one
            if output_file is None:
                output_file = Path("output_elevenlabs.wav")
            
            self.logger.info(f"🔄 Calling ElevenLabs TTS API for text: {text[:50]}...")
            
            # Make the API call with retry logic
            success = self._make_api_call(text, voice_id, output_file)
            
            if success:
                duration = self.estimate_duration(text)
                file_size = output_file.stat().st_size
                self.logger.info(f"✅ ElevenLabs synthesis successful: {output_file} "
                               f"({file_size/1024:.1f}KB, {duration:.2f}s)")
                return True
            else:
                self.logger.error(f"❌ ElevenLabs synthesis failed after retries")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ ElevenLabs synthesis error: {e}")
            return False

    def synthesize_with_metadata(self, text: str, voice: str = None, output_file: Path = None) -> Dict[str, Any]:
        """
        Synthesize speech and return metadata about the synthesis.
        
        Args:
            text: The text to convert to speech
            voice: Voice ID to use (defaults to the one in config or default_voice_id)
            output_file: Path to save the output audio file
            
        Returns:
            dict: Dictionary containing synthesis metadata
        """
        if output_file is None:
            output_file = Path("output_elevenlabs.wav")
            
        success = self.synthesize(text, voice, output_file)
        
        return {
            'success': success,
            'text': text,
            'voice': voice or self.default_voice_id,
            'output_file': str(output_file.absolute()),
            'provider': self.name,
            'model': self.model_id,
            'estimated_duration': self.estimate_duration(text),
            'error': None if success else "Synthesis failed",
            'file_info': self.get_file_info(output_file) if success else {}
        }

    def clone(self, text: str, reference_audio: Path, output_file: Path) -> bool:
        """
        Clone a voice from reference audio.
        Note: This is a placeholder. Voice cloning requires additional setup with ElevenLabs.
        """
        self.logger.warning("❌ Voice cloning requires additional setup with ElevenLabs")
        return False
