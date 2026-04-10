#!/usr/bin/env python3
# ============================================================
# ElevenLabs Provider Test
# Test ElevenLabs TTS Provider
# ============================================================

import os
import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
# sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("test_output/elevenlabs_test.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_elevenlabs_tts():
    """
    Test ElevenLabs TTS Provider with a simple text.
    """
    print("🧪 Testing ElevenLabs TTS Provider...")

    # Configure output
    output_dir = Path("test_output/elevenlabs_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test text in Vietnamese
    test_text = "Xin chào, đây là test với ElevenLabs TTS provider"
    test_texts = [
        ('0108245608', 'số sáu mươi sáu, đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội'),
        ('0108235818', 'số ba trăm chín mươi tám đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội')
    ]

    # Configure ElevenLabs provider
    providers_config = {
        "elevenlabs": {
            "api_key": os.getenv("ELEVENLABS_API_KEY"),
            "model": "eleven_v3",
            "voice": "Rachel",
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    try:
        # Initialize generator
        generator = DatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config
        )

        # Test generation with ElevenLabs
        summary = generator.generate_from_text_list(
            text_items=test_texts,
            provider_model_voice=("elevenlabs", "eleven_v3", "pNInz6obpgDQGcFmaJgB"),
            batch_size=1,
            delay_between_requests=2.0
        )

        # Check results
        if summary.successful_generations > 0:
            result = summary.results[0]
            print("✅ ElevenLabs Provider test SUCCESSFUL!")
            print(f"📁 Audio file: {result.audio_path}")
            print(f"⏱️ Duration: {result.duration:.2f}s")
            
            if result.audio_path.exists():
                file_size = result.audio_path.stat().st_size
                print(f"📊 File size: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"❌ Test failed: {summary.errors}")
            return False

    except Exception as e:
        print(f"❌ Error testing ElevenLabs Provider: {e}")
        return False

def main():
    """Run all ElevenLabs tests"""
    print("\n🎯 ElevenLabs Provider Test Suite")
    print("=" * 50 + "\n")
    
    setup_logging()
    
    test_results = {}
    
    print("\n" + "=" * 50)
    print("Running: Basic TTS")
    print("=" * 50 + "\n")
    
    test_results["Basic TTS"] = test_elevenlabs_tts()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 ELEVENLABS TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print("\n🎉 All ElevenLabs tests PASSED!")
    else:
        print("\n⚠️ Some tests failed. Please check ELEVENLABS_API_KEY and network connection.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
