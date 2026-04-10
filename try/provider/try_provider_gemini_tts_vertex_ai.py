import os
from datetime import datetime
from pathlib import Path

from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig, VoiceConfig, AudioConfig
from speech_synth_engine.schemas.generation import GenerateSpeechConfig
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider
from rich import print

# ================= Vertex AI Credentials Setup =================
# Prefer using environment variables for credentials
# Uncomment and set your actual paths/IDs if needed:
# os.environ["GCP_CREDENTIALS_PATH"] = "/absolute/path/to/your-service-account.json"
# os.environ["GCP_PROJECT_ID"] = "your-gcp-project-id"
# os.environ["GCP_LOCATION"] = "us-central1"  # optional, defaults to us-central1

credentials_cfg = CredentialsConfig(
    # The provider will look for these envs. Names are flexible but must include hints:
    # - contains 'json' -> credentials_path
    # - contains 'project' -> project_id
    # - contains 'location' -> location
    envs=["GCP_CREDENTIALS", "GCP_PROJECT_ID", "GCP_LOCATION", "USE_VERTEX_AI"],
)

provider_cfg = ProviderConfig(
    name="gemini-vertex",
    models=["gemini-2.5-flash-preview-tts"],
    default_model="gemini-2.5-flash-preview-tts",
    credentials=credentials_cfg,
)

# ================= Per-request generation config =================
voice_cfg = VoiceConfig(
    # voice_id="Orus"
)
audio_cfg = AudioConfig(channel=1, sample_rate=24000)
generation_cfg = GenerateSpeechConfig(
    model="gemini-2.5-flash-preview-tts",
    voice_config=voice_cfg,
    audio_config=audio_cfg,
)

# ================= Provider init (Vertex AI) =================
provider = GeminiTTSProvider(provider_config=provider_cfg)

# ================= Output path (standardized) =================
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
text = f"Xin chào, đây là giọng nói Gemini (Vertex AI) vào lúc {current_time}"
text_in_filename = "_".join(text[:50].split())
output_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/try/try_output/provider/try_gemini_vertex_ai_tts/wavs")
output_file = output_dir / f"try_gemini_vertex_ai_{text_in_filename}_{current_time}.wav"

# ================= Run synthesis =================
result = provider.synthesize_with_metadata(
    text=text,
    output_file=output_file,
    generation_config=generation_cfg,
)

print("Success:", result)



# # Thiết lập biến môi trường nếu cần
# export USE_VERTEX_AI=True
# export GCP_CREDENTIALS="/home/nampv1/keys/namhocayai_vnpost-tts-e1b103363c0d.json"
# export GCP_PROJECT_ID="vnpost-tts"
# export GCP_LOCATION="us-central1"  # tùy chọn

# # Chạy script
# PYTHONPATH=. python try/provider/try_provider_gemini_tts_vertex_ai.py
