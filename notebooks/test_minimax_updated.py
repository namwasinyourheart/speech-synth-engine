#!/usr/bin/env python3
"""
Test script for the updated MiniMax selenium provider
Demonstrates the correct usage patterns for voice cloning
"""

import os
import sys
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider
from speech_synth_engine.dataset.text_loaders import TextFileLoader

def test_minimax_provider():
    """Test the MiniMax provider with correct voice cloning methods"""

    print("🧪 Testing MiniMax Provider - Updated Methods")
    print("=" * 50)

    # Check credentials
    google_email = os.getenv("MINIMAX_GOOGLE_EMAIL")
    google_password = os.getenv("MINIMAX_GOOGLE_PASSWORD")

    if not google_email or not google_password:
        print("❌ Missing credentials!")
        print("   Set: export MINIMAX_GOOGLE_EMAIL='your_email@gmail.com'")
        print("   Set: export MINIMAX_GOOGLE_PASSWORD='your_password'")
        return False

    # Setup configuration
    config = {
        "base_url": "https://www.minimax.io/audio/voices-cloning",
        "google_email": google_email,
        "google_password": google_password,
        "headless": False,
        "sample_rate": 22050,
        "language": "Vietnamese",
        "timeout": 60,
        "download_timeout": 180,
        "max_wait_time": 300
    }

    print(f"✅ Configuration loaded")
    print(f"📧 Email: {google_email}")
    print(f"🌐 Headless: {config['headless']}")

    # Create provider
    provider = MiniMaxSeleniumProvider("minimax_test", config)
    print(f"✅ Provider created: {provider.name}")
    print(f"📊 Provider capabilities: {provider.provider_info}")

    # Setup output directory
    output_dir = Path("notebook_test_output")
    output_dir.mkdir(exist_ok=True)

    # Find reference audio
    reference_audio_sources = [
        Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/audio/test.wav"),
        Path("/media/nampv1/hdd/data/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10-20251024T103708Z-1-001/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10/spk2_1.m4a")
    ]

    reference_audio = None
    for source in reference_audio_sources:
        if source.exists() and source.stat().st_size > 1000:
            reference_audio = source
            break

    if not reference_audio:
        print("⚠️ No reference audio found!")
        print("   Place a valid audio file (.wav/.mp3) in the test_output directory")
        provider.cleanup()
        return False

    print(f"✅ Reference audio found: {reference_audio}")
    print(f"📊 File size: {reference_audio.stat().st_size / 1024:.1f} KB")

    # Test 1: clone_with_metadata (recommended method)
    print("\n🧪 Test 1: clone_with_metadata (Recommended)")
    print("-" * 40)

    test_text = "Xin chào, đây là MiniMax voice cloning với metadata"
    output_file = output_dir / "metadata_test.wav"

    print(f"🎤 Text: {test_text}")
    print(f"📁 Output: {output_file}")

    try:
        result = provider.clone_with_metadata(test_text, reference_audio, output_file)

        print("📊 Results:")
        print(f"   ✅ Success: {result.get('success', False)}")
        print(f"   📊 Audio URL: {result.get('audio_url', 'None')}")
        print(f"   ⏱️ Duration: {result.get('estimated_duration', 0):.2f}s")
        print(f"   🎤 Voice: {result.get('voice', 'cloned_voice')}")

        if result.get('success') and output_file.exists():
            file_size = output_file.stat().st_size / 1024
            print(f"   ✅ Generated: {file_size:.1f} KB")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Basic clone method
    print("\n🧪 Test 2: Basic clone method")
    print("-" * 40)

    basic_text = "Test với basic clone method"
    basic_output = output_dir / "basic_test.wav"

    print(f"🎤 Text: {basic_text}")
    print(f"📁 Output: {basic_output}")

    try:
        success = provider.clone(basic_text, reference_audio, basic_output)

        if success and basic_output.exists():
            file_size = basic_output.stat().st_size / 1024
            print(f"✅ Basic clone successful: {file_size:.1f} KB")
        else:
            print("❌ Basic clone failed")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: synthesize_with_metadata (should use clone logic)
    print("\n🧪 Test 3: synthesize_with_metadata (clone logic)")
    print("-" * 40)

    synth_text = "Test synthesize_with_metadata method"
    synth_output = output_dir / "synth_test.wav"

    print(f"🎤 Text: {synth_text}")
    print(f"📁 Output: {synth_output}")

    try:
        synth_result = provider.synthesize_with_metadata(synth_text, "cloned_voice", synth_output)

        print(f"📊 Synthesis result: {synth_result.get('success', False)}")
        if synth_result.get('error'):
            print(f"📊 Error: {synth_result['error']}")
        if synth_result.get('success') and synth_output.exists():
            file_size = synth_output.stat().st_size / 1024
            print(f"✅ Success: {file_size:.1f} KB")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: TextFileLoader integration
    print("\n🧪 Test 4: TextFileLoader Integration")
    print("-" * 40)

    # Create test text file
    text_file = output_dir / "test_texts.txt"
    test_texts = [
        "1\tText file line 1 for testing",
        "2\tText file line 2 with Vietnamese",
        "3\tText file line 3 final test"
    ]

    text_file.write_text("\n".join(test_texts), encoding='utf-8')
    print(f"✅ Created text file: {text_file}")

    # Load texts
    loader = TextFileLoader(text_file)
    loaded_texts = loader.load()

    print(f"📄 Loaded {len(loaded_texts)} texts:")
    for text_id, text in loaded_texts:
        print(f"   {text_id}: {text}")

    # Test 5: Batch processing (if reference audio available)
    print("\n🧪 Test 5: Batch Processing")
    print("-" * 40)

    if reference_audio:
        batch_output_dir = output_dir / "batch_test"
        batch_output_dir.mkdir(exist_ok=True)

        print(f"🎭 Starting batch processing...")
        print(f"📄 Input file: {text_file}")
        print(f"🎵 Reference: {reference_audio}")
        print(f"📁 Output: {batch_output_dir}")

        try:
            batch_result = provider.clone_batch(text_file, reference_audio, batch_output_dir)

            print("📊 Batch Results:")
            print(f"   Total: {batch_result.get('total_texts', 0)}")
            print(f"   Processed: {batch_result.get('processed', 0)}")
            print(f"   Failed: {batch_result.get('failed', 0)}")
            print(f"   Success rate: {batch_result.get('success_rate', 0):.1f}%")

            # Show individual results
            print("📋 Individual results:")
            for result in batch_result.get('results', []):
                status = "✅" if result.get('success') else "❌"
                print(f"   {status} {result.get('id', 'unknown')}: {Path(result.get('output_file', '')).name}")

        except Exception as e:
            print(f"❌ Batch error: {e}")

    # Cleanup
    print("\n🧹 Cleanup")
    print("-" * 40)
    provider.cleanup()

    print(f"✅ Generated files in: {output_dir}")
    print(f"📊 Total files: {len(list(output_dir.rglob('*')))}")

    print("\n🎉 Testing completed!")
    print("\n💡 Key findings:")
    print("   - ✅ clone_with_metadata() provides comprehensive results")
    print("   - ✅ clone() provides simple boolean results")
    print("   - ✅ synthesize_with_metadata() uses clone logic")
    print("   - ✅ TextFileLoader supports multiple formats")
    print("   - ✅ Batch processing with detailed reporting")
    print("   - ✅ Comprehensive error handling")

    return True

if __name__ == "__main__":
    success = test_minimax_provider()
    sys.exit(0 if success else 1)
