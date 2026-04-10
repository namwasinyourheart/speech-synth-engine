import os
import sys
from datetime import datetime

# Add speech-synth-engine to path
# sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.gtts_provider import GTTSProvider
from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig, VoiceConfig
from speech_synth_engine.schemas.generation import GenerateSpeechConfig

# Tạo provider_config chuẩn cho GTTS
provider_config = ProviderConfig(
    name="gtts",
    models=["default"],
    default_model="default",
    credentials=CredentialsConfig()
)

voice_cfg = VoiceConfig(voice_id="vi")
generation_cfg = GenerateSpeechConfig(
    model="default",
    voice_config=voice_cfg
)

from pathlib import Path
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
text = "Xin chào, đây là giọng nói được tạo ra bởi gTTS provider vào lúc " + current_time

text_in_filename = "_".join(text[:50].split())
output_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/try/try_output/provider/try_gtts/wavs")
output_file = output_dir / f"try_gtts_{text_in_filename}_{current_time}.wav"

gtts = GTTSProvider("gtts", provider_config=provider_config)

result = gtts.synthesize(text, output_file, generation_config=generation_cfg)
if result:
    print(f"✅ GTTS synthesis success! Output: {output_file}")
else:
    print(f"❌ GTTS synthesis failed!")
