import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the project root directory to the Python path
# sys.path.append(os.path.abspath(os.path.join(__file__, "../../")))

import os
import tempfile
from gtts import gTTS
from pydub import AudioSegment
from typing import Optional
from ..providers.base.provider import TTSProvider

class GTTSProvider(TTSProvider):
    """
    TTS provider using Google Text-to-Speech (gTTS).
    Updated to inherit from TTSProvider with full enhanced features.
    """

    def __init__(self, name: str = "gtts", provider_config: Any = None):
        """
        GTTSProvider đồng bộ interface với các provider khác, không lấy language/sample_rate từ provider_config.
        Language và sample_rate sẽ lấy qua VoiceConfig/AudioConfig khi synthesize.
        """
        super().__init__(name, {"provider_config": provider_config} if provider_config else {})
        self.provider_config = provider_config
        # Track last error for detailed error reporting
        self.last_error: Optional[str] = None
        # Không lấy self.lang, self.sample_rate ở đây nữa

    def _get_supported_voices(self) -> List[str]:
        """GTTS supports Vietnamese by default"""
        return ["vi"]

    def synthesize(self, text: str, output_file: str | Path, generation_config: Any = None, **kwargs) -> bool:
        """
        Chuẩn hóa interface synthesize: nhận text, output_file, generation_config (chuẩn hệ thống provider).
        - Lấy language từ generation_config.voice_config.voice_id nếu có, mặc định 'vi'.
        - Lấy sample_rate từ generation_config.audio_config nếu có, mặc định 22050.
        """
        # Clear any previous error
        self.last_error = None
        
        try:
            # Validate text before synthesizing
            if not self.validate_text(text):
                self.last_error = f"Invalid text: {text[:50]}..."
                self.logger.error(self.last_error)
                return False

            # Resolve voice/language
            lang = 'vi'
            if generation_config and getattr(generation_config, 'voice_config', None):
                lang = getattr(generation_config.voice_config, 'voice_id', 'vi')
            # GTTS chỉ cần lang, không quan tâm sample_rate/audio_config
            sample_rate = 22050  # giữ để không lỗi đoạn pydub, nhưng không lấy từ audio_config

            # Validate voice
            if lang not in self.supported_voices:
                self.last_error = f"Voice '{lang}' is not supported. Available voices: {self.supported_voices}"
                self.logger.error(self.last_error)
                return False

            # Normalize output path and ensure directory exists
            output_path = Path(output_file) if isinstance(output_file, str) else output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create temporary MP3 file from gTTS
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                mp3_path = tmp_mp3.name

            try:
                # Create gTTS object and save MP3
                tts = gTTS(text=text, lang=lang)
                tts.save(mp3_path)

                # Read MP3 and convert to WAV with configured sample rate
                audio = AudioSegment.from_mp3(mp3_path)

                # Set sample rate according to config
                audio = audio.set_frame_rate(sample_rate)

                # Save WAV
                audio.export(str(output_path), format="wav")

                # Enhanced: return success/failure with detailed information
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    self.logger.info(f"GTTS synthesis successful: {output_path} ({file_size/1024:.1f}KB)")
                    return True
                else:
                    self.last_error = f"GTTS file was not created: {output_path}"
                    self.logger.error(f"❌ {self.last_error}")
                    return False

            finally:
                # Delete temporary MP3 file
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)

        except Exception as e:
            self.last_error = f"GTTS synthesis error: {e}"
            self.logger.error(f"❌ {self.last_error}")
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
