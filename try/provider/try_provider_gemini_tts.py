import sys
import os

# # # sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime
from pathlib import Path
from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig
from speech_synth_engine.schemas.provider import VoiceConfig, AudioConfig
from speech_synth_engine.schemas.generation import GenerateSpeechConfig
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider
from rich import print

# Build configs
credentials_cfg = CredentialsConfig(
    envs=["GEMINI_API_KEY", "GCP_CREDENTIALS", "GCP_PROJECT_ID", "GCP_LOCATION"],
    api_keys=[
        # "AIzaSyDR7graWD7CXcLphBrcg4jB8l8Q2Zil26Y", 
        "AIzaSyBS012-hXDQb_WwNtavE19W6t3LcE5VRVQ", 
        # "AIzaSyA1l0Y1y4Rv6UqsrmOYeH4Dnlo-4LX02xU"
    ],
    
)

pcfg = ProviderConfig(
    name="gemini",
    models=["gemini-2.5-flash-preview-tts"],
    default_model="gemini-2.5-flash-preview-tts",
    credentials=credentials_cfg,
)

# Optional per-request configs
voice_cfg = VoiceConfig(
    # voice_id="Orus"
)
audio_cfg = AudioConfig(
    channel=1, 
    sample_rate=24000
)
generation_cfg = GenerateSpeechConfig(
    model="gemini-2.5-flash-preview-tts",
    voice_config=voice_cfg,
    audio_config=audio_cfg,
)

provider = GeminiTTSProvider(provider_config=pcfg)

from speech_synth_engine.utils import time_to_vietnamese_spoken

current_time = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
current_time_spoken = time_to_vietnamese_spoken(current_time)
text = f"Xin chào, đây là giọng nói Gemini được tạo ra vào lúc {current_time_spoken}"
text_in_filename = "_".join(text[:50].split())
output_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/try/try_output/provider/try_gemini_tts/wavs")
ok = provider.synthesize_with_metadata(
    text=text,
    output_file=output_dir / f"try_gemini_{text_in_filename}_{current_time}.wav",
    generation_config=generation_cfg,
)
print("Success:", ok)