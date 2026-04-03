import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from speech_synth_engine.providers.elevenlabs_provider import ElevenLabsProvider

# Configuration for the ElevenLabs TTS provider
config = {
    'api_key': os.getenv('ELEVENLABS_API_KEY'),  # Get from environment variable
    'model_id': 'eleven_v3',
    "language_code": "vi",
    'default_voice_id': 'BlZK9tHPU6XXjwOSIiYA'  # Rachel's voice
}

def main():
    try:
        # Initialize the provider
        tts = ElevenLabsProvider(name="elevenlabs-tts", config=config)
        
        # List available voices (first 5 for brevity)
        print("Available voices (first 5):")
        
        # Ensure we have a client before proceeding
        if not hasattr(tts, 'client') or tts.client is None:
            print("⚠️  Warning: ElevenLabs client not properly initialized. Using default voices.")
            voices = [
                'pNInz6obpgDQGcFmaJgB',  # Rachel
                # 'MF3mGyEYCl7XYWbV9V6O',  # Domi
                # 'D38z5RcWu1voky8WS1ja',  # Bella
                # 'XrExE9yKIg1WjnnlVkGX',  # Antoni
                # 'VR6AewLTigWG4xSOukaG',  # Elli
            ]
        else:
            voices = tts.supported_voices[:5]  # Get first 5 voices
            
        for i, voice in enumerate(voices, 1):
            print(f"{i}. {voice}")

        print("Number of voices:", len(tts.supported_voices))
        
        # Example text to synthesize
        text = """
        Hello! This is a demonstration of the ElevenLabs TTS provider.
        """

        text = """số một, ngách tám mươi tám trên năm, ngõ tám mươi tám, đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội
        """
        # text = "good morning"
        # text = "xin chào việt nam"
        # Output file
        import time
        current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
        output_file = Path(f"/home/nampv1/projects/tts/speech-synth-engine/test_output/output_elevenlabs_{current_time}.wav")
        
        # Select a voice (using the first available voice as default)
        selected_voice = voices[0] if voices else config['default_voice_id']
        # selected_voice = "puBBfOSRT9Dbk3FUJQGd"
        print(f"\nSynthesizing with voice: {selected_voice}")
        
        # Synthesize speech with metadata
        metadata = tts.synthesize_with_metadata(
            text=text,
            voice=selected_voice,
            output_file=output_file
        )
        
        if metadata['success']:
            print(f"\n✅ Success! Audio saved to: {output_file.absolute()}")
            print("\nSynthesis metadata:")
            for key, value in metadata.items():
                if key != 'file_info':  # Print file_info separately for better formatting
                    print(f"{key}: {value}")
            
            # Print file info with indentation
            print("\nFile info:")
            for key, value in metadata['file_info'].items():
                print(f"  {key}: {value}")
        else:
            print("\n❌ Synthesis failed")
            if 'error' in metadata:
                print(f"Error: {metadata['error']}")
                
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return

if __name__ == "__main__":
    main()
