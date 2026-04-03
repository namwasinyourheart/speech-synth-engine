import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from pathlib import Path
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

# Khởi tạo GeminiTTSProvider

config = {
    'use_vertex_ai': True,
    'credentials_path': '/home/nampv1/projects/tts/speech-synth-engine/notebooks/learn-gcp-first-project-202506-fe9cece37e90.json',
    'project_id': 'learn-gcp-first-project-202506',
    'location': 'global',  # Optional, defaults to us-central1
    'model': 'gemini-2.5-flash-preview-tts',
    # 'sample_rate': 24000
}
gemini = GeminiTTSProvider(config=config)
voice = "Aoede"

# Câu test
text = "Đây là giọng nói tổng hợp được sinh ra bởi giọng " + voice

# Output file
output_file = Path("test_output.wav")

# Generate audio
try:
    gemini.synthesize(text, voice=voice, output_file=output_file)
    print(f"Audio generated successfully: {output_file}")
except Exception as e:
    print(f"Error: {e}")
