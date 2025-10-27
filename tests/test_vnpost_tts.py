import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider

# Khởi tạo provider
vnpost = VnPostTTSProvider()

# Sử dụng
vnpost.synthesize(
    text="Xin chào, đây là giọng nói tổng hợp được sinh ra từ VnPost TTS",
    voice="Hà My",
    output_file="synthesized_output.wav"
)

# vnpost.clone(
#     text="Xin chào, đây là giọng nói được clone.",
#     reference_audio="/home/nampv1/projects/tts/tts-ft/ZipVoice/demo/backend/voices/laivansam_15s.mp3",
#     output_file="cloned_output.wav"
# )