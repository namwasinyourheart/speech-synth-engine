from pathlib import Path
import os
import wave
from google import genai
from google.genai import types
from typing import Dict, List, Any
from ..providers.base.provider import TTSProvider

from dotenv import load_dotenv
load_dotenv()

class GeminiTTSProvider(TTSProvider):
    """
    TTS provider using Google Gemini TTS.
    Updated to inherit from TTSProvider with full enhanced features.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        # Initialize TTSProvider with name and config
        super().__init__(name, config)

        # Initialize Gemini client with API key from environment or config
        api_key = os.getenv('GEMINI_API_KEY') or self.config.get('api_key')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable or config is required")

        self.client = genai.Client(api_key=api_key)

        # Enhanced features from config
        self.model = self.config.get('model', 'gemini-2.5-flash-preview-tts')
        self.sample_rate = self.config.get('sample_rate', 24000)

    def _get_supported_voices(self) -> List[str]:
        """Gemini TTS supports multiple multilingual voices"""
        # Basic voice list, can be extended based on actual API 
        supported_voices = [
            "Zephyr",
            "Puck",
            "Charon",
            "Kore",
            "Fenrir",
            "Leda",
            "Callirrhoe",
            "Despina",
            "Erinome",
            "Umbriel",
            "Algieba",
            "Iapetus",
            "Enceladus",
            "Algenib",
            "Rasalgethi",
            "Laomedeia",
            "Schedar",
            "Gacrux",
            "Pulcherrima",
            "Achird",
            "Zubenelgenubi",
            "Vindemiatrix",
            "Sadachbia",
            "Sadaltager",
            "Sulafat"
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

    def synthesize(self, text: str, voice: str, output_file: Path) -> bool:
        """
        Enhanced synthesize with validation and improved error handling.
        """
        try:
            # Validate text before synthesizing
            if not self.validate_text(text):
                self.logger.error(f"Invalid text: {text[:50]}...")
                return False

            # Validate voice
            if voice not in self.supported_voices:
                self.logger.error(f"Voice '{voice}' is not supported. Available voices: {self.supported_voices}")
                return False

            self.logger.info(f"🔄 Calling Gemini TTS API for text: {text[:50]}...")

            # Call Gemini TTS API with enhanced configuration
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

            # Get PCM bytes from response
            pcm_data = response.candidates[0].content.parts[0].inline_data.data

            # Save WAV with configured sample rate
            self.save_wave(str(output_file), pcm_data, rate=self.sample_rate)

            # Enhanced: check if file was created and log detailed information
            if output_file.exists():
                file_size = output_file.stat().st_size
                duration = self.estimate_duration(text)
                self.logger.info(f"✅ Gemini synthesis successful: {output_file} ({file_size/1024:.1f}KB, {duration:.2f}s)")
                return True
            else:
                self.logger.error(f"❌ Gemini file was not created: {output_file}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Gemini synthesis error: {e}")
            return False

    def clone(self, text: str, reference_audio: Path, output_file: Path) -> bool:
        """
        Enhanced clone - Gemini TTS does not support voice cloning.
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
