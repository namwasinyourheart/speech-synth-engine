import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(__file__, "../../")))

import os
import tempfile
from gtts import gTTS
from pydub import AudioSegment
from ..providers.base.provider import TTSProvider

class GTTSProvider(TTSProvider):
    """
    TTS provider using Google Text-to-Speech (gTTS).
    Updated to inherit from TTSProvider with full enhanced features.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        # Initialize TTSProvider with name and config
        super().__init__(name, config)

        # Get language from config or default to 'vi'
        self.lang = self.config.get('language', 'vi')

        # Enhanced features from config
        self.sample_rate = self.config.get('sample_rate', 22050)

    def _get_supported_voices(self) -> List[str]:
        """GTTS supports Vietnamese by default"""
        return ["vi"]

    def synthesize(self, text: str, voice: str, output_file: Path) -> bool:
        """
        Synthesize with validation and improved error handling.
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

            # Create temporary MP3 file from gTTS
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                mp3_path = tmp_mp3.name

            try:
                # Create gTTS object and save MP3
                tts = gTTS(text=text, lang=self.lang)
                tts.save(mp3_path)

                # Read MP3 and convert to WAV with configured sample rate
                audio = AudioSegment.from_mp3(mp3_path)

                # Set sample rate according to config
                audio = audio.set_frame_rate(self.sample_rate)

                # Save WAV
                audio.export(str(output_file), format="wav")

                # Enhanced: return success/failure with detailed information
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    duration = self.estimate_duration(text)
                    self.logger.info(f"✅ GTTS synthesis successful: {output_file} ({file_size/1024:.1f}KB, {duration:.2f}s)")
                    return True
                else:
                    self.logger.error(f"❌ GTTS file was not created: {output_file}")
                    return False

            finally:
                # Delete temporary MP3 file
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)

        except Exception as e:
            self.logger.error(f"❌ GTTS synthesis error: {e}")
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
            'language': self.lang,
            'estimated_duration': self.estimate_duration(text),
            'error': None if success else "Synthesis failed",
            'file_info': self.get_file_info(output_file) if success else {}
        }
