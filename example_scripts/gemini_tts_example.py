import sys
import os
import time
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

import logging

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Configuration for the Gemini TTS provider
config = {
    # 'api_key': 'your-api-key-here',  # Or set GEMINI_API_KEY environment variable
    'model': 'gemini-2.5-flash-tts',
    'use_vertex_ai': True,
    'credentials_path': '/home/nampv1/projects/tts/speech-synth-engine/notebooks/learn-gcp-first-project-202506-fe9cece37e90.json',
    'project_id': 'learn-gcp-first-project-202506',
    'sample_rate': 24000
}

def main():
    # Initialize the provider
    tts = GeminiTTSProvider(name="gemini-tts", config=config)
    
    # List available voices
    print("Available voices:")
    for i, voice in enumerate(tts.supported_voices, 1):
        print(f"{i}. {voice}")
    
    # Example text to synthesize
    text = "Hello, this is a test of the Gemini TTS provider. I can speak in multiple voices and languages."
    
    current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
    test_output_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/test_output")
    # Output file
    output_file = Path(f"{test_output_dir}/output_gemini_tts_{current_time}.wav")
    
    # Select a voice (using the first available voice as default)
    selected_voice = tts.supported_voices[-1]
    print(f"\nSynthesizing with voice: {selected_voice}")
    
    # Synthesize speech
    result = tts.synthesize(
        text=text,
        voice=selected_voice,
        output_file=output_file
    )
    
    if result:
        print(f"\n✅ Success! Audio saved to: {output_file.absolute()}")
        print("\nSynthesis metadata:")
        metadata = tts.synthesize_with_metadata(text, selected_voice, output_file)
        for key, value in metadata.items():
            print(f"{key}: {value}")
    else:
        print("\n❌ Synthesis failed")

if __name__ == "__main__":
    main()
