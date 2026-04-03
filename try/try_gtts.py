import os
import sys

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.gtts_provider import GTTSProvider

gtts = GTTSProvider("gtts")

print(gtts._get_supported_voices())

text = "Xin chào, đây là giọng nói được tạo ra bởi gTTS provider"
voice = "vi"
model = "default"
output_file = "/home/nampv1/projects/tts/speech-synth-engine/try/output/try_gtts.wav"      

gtts.synthesize(text, voice, output_file)

