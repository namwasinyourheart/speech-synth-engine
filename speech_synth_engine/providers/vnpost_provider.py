import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..providers.base.provider import TTSProvider

class VnPostTTSProvider(TTSProvider):
    """
    TTS provider using VNPost TTS API.
    Updated to inherit from TTSProvider with full enhanced features.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        # Initialize TTSProvider with name and config
        super().__init__(name, config)

        # Get API URLs from config or default
        self.api_url = self.config.get('api_url', 'https://ai.vnpost.vn/voiceai/core/tts/v1/synthesize')
        self.clone_api_url = self.config.get('clone_api_url', 'https://ai.vnpost.vn/voiceai/core/tts/v1/clone')

        # Enhanced features from config
        self.sample_rate = self.config.get('sample_rate', 22050)
        self.default_voice = self.config.get('voice', 'Hà My')
        
        # Track last error for detailed error reporting
        self.last_error: Optional[str] = None

    def _get_supported_voices(self) -> List[str]:
        """VNPost supports multiple Vietnamese voices"""
        return ["Hà My", "Minh Tuấn", "Bảo Khang", "Lan Chi", "Tuấn Kiệt", "Ngọc Ánh"]

    def synthesize(self, text: str, voice: str, output_file: Path) -> bool:
        """
        Synthesize with validation and improved error handling.
        """
        # Clear any previous error
        self.last_error = None
        
        try:
            # Validate text before synthesizing
            if not self.validate_text(text):
                self.last_error = f"Invalid text: {text[:50]}..."
                self.logger.error(self.last_error)
                return False

            # Validate voice
            if voice not in self.supported_voices:
                self.last_error = f"Voice '{voice}' is not supported. Voices available: {self.supported_voices}"
                self.logger.error(self.last_error)
                return False

            # Prepare form data
            files = {
                "text": (None, text),
                "voice": (None, voice)
            }

            # Call API with timeout and improved error handling
            self.logger.info(f"🔄 Calling VNPost TTS API for text: {text[:50]}...")

            response = requests.post(
                self.api_url,
                files=files,
                timeout=30  # Enhanced: timeout to avoid hang
            )

            if response.status_code != 200:
                self.last_error = f"VNPost TTS API error: {response.status_code}, {response.text}"
                self.logger.error(f"❌ {self.last_error}")
                return False

            # Save response content (WAV file) to output file
            with open(output_file, "wb") as f:
                f.write(response.content)

            # Enhanced: check if file is created and log detailed information
            if output_file.exists():
                file_size = output_file.stat().st_size
                self.logger.info(f"VNPost synthesis successful: {output_file} ({file_size/1024:.1f}KB)")
                return True
            else:
                self.last_error = f"VNPost file not created: {output_file}"
                self.logger.error(f"❌ {self.last_error}")
                return False

        except requests.exceptions.Timeout:
            self.last_error = "VNPost API timeout"
            self.logger.error(f"❌ {self.last_error}")
            return False
        except requests.exceptions.RequestException as e:
            self.last_error = f"VNPost API request error: {e}"
            self.logger.error(f"❌ {self.last_error}")
            return False
        except Exception as e:
            self.last_error = f"VNPost synthesize error: {e}"
            self.logger.error(f"❌ {self.last_error}")
            return False

    def clone(self, text: str, reference_audio: Path, output_file: Path) -> bool:
        """
        Clone voice from reference audio.
        Provider which does not support cloning will raise NotImplementedError.
        """
        try:
            # Validate inputs
            if not self.validate_text(text):
                self.logger.error("Invalid text for clone")
                return False

            if not reference_audio.exists():
                self.logger.error(f"Reference audio does not exist: {reference_audio}")
                return False

            # Prepare form data
            files = {
                "text": (None, text),
                "reference_audio": open(reference_audio, "rb")
            }

            self.logger.info(f"🔄 Calling VNPost Clone API...")

            # Call Clone API
            response = requests.post(
                self.clone_api_url,
                files=files,
                timeout=60  # Clone may take longer time
            )

            if response.status_code != 200:
                self.logger.error(f"❌ VNPost Clone API error: {response.status_code}, {response.text}")
                return False

            # Save response content (WAV file) to output file
            with open(output_file, "wb") as f:
                f.write(response.content)

            if output_file.exists():
                file_size = output_file.stat().st_size
                self.logger.info(f"✅ VNPost cloning successful: {output_file} ({file_size/1024:.1f}KB)")
                return True
            else:
                self.logger.error(f"❌ VNPost cloning failed: {output_file}")
                return False

        except Exception as e:
            self.logger.error(f"❌ VNPost cloning error: {e}")
            return False

    def synthesize_with_metadata(self, text: str, voice: str, output_file: Path) -> Dict[str, Any]:
        """
        Synthesize with comprehensive metadata information (compatible with enhanced system).
        """
        success = self.synthesize(text, voice, output_file)

        from speech_synth_engine.schemas.schemas import SynthesisResult
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
