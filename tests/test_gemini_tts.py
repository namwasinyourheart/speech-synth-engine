import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from pathlib import Path
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

# Khởi tạo GeminiTTSProvider
gemini = GeminiTTSProvider()

# Câu test
text = "Đây là giọng nói tổng hợp được sinh ra"

# Output file
output_file = Path("test_output.wav")

# Generate audio
try:
    gemini.synthesize(text, voice="aoede", output_file="test_output.wav")
    print(f"Audio generated successfully: {output_file}")
except Exception as e:
    print(f"Error: {e}")
