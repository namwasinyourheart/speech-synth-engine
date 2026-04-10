import sys
import os
import time
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

GCP_CREDENTIALS_PATH="/home/nampv1/projects/raggg/gcp_key.json"
GCP_LOCATION = "global"
GCP_PROJECT_ID = "qwiklabs-gcp-02-469ca13f57ec"

config = {
    'use_vertex_ai': False,
    'api_keys': 'AIzaSyBS012-hXDQb_WwNtavE19W6t3LcE5VRVQ',
    # 'credentials_path': '/home/nampv1/projects/raggg/gcp_key.json',
    # 'project_id': 'qwiklabs-gcp-02-469ca13f57ec',
    # 'location': 'global',
    'model': 'gemini-2.5-flash-preview-tts',
    # 'sample_rate': 24000
}

tts = GeminiTTSProvider(name="gemini-tts", config=config)

print(tts.supported_voices)

voice = "Aoede"
text = "Đây là giọng nói tổng hợp được sinh ra bởi giọng " + voice

# Output file
output_file = "/home/nampv1/projects/tts/speech-synth-engine/try/output/try_gemini_tts.wav"

# Generate audio
try:
    tts.synthesize(text, voice=voice, output_file=output_file)
    print(f"Audio generated successfully: {output_file}")
except Exception as e:
    print(f"Error: {e}")