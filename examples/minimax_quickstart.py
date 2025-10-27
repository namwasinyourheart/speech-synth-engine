#!/usr/bin/env python3
"""
MiniMax Selenium Provider - Quick Start Example

This script demonstrates basic usage of the MiniMax selenium provider
for voice cloning and text-to-speech synthesis.
"""

import os
import sys
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider
from speech_synth_engine.dataset.text_loaders import TextFileLoader


def main():
    print("🚀 MiniMax Selenium Provider - Quick Start")
    print("=" * 50)

    # Check credentials
    google_email = os.getenv("MINIMAX_GOOGLE_EMAIL", "signupwithnamm@gmail.com")
    google_password = os.getenv("MINIMAX_GOOGLE_PASSWORD", "mailthanhthuy667")

    if not google_email or not google_password:
        print("❌ Missing credentials!")
        print("   Please set environment variables:")
        print("   export MINIMAX_GOOGLE_EMAIL='your_email@gmail.com'")
        print("   export MINIMAX_GOOGLE_PASSWORD='your_password'")
        return

    # Setup configuration
    config = {
        "base_url": "https://www.minimax.io/audio/voices-cloning",
        "google_email": google_email,
        "google_password": google_password,
        "headless": False,  # Set to True for headless mode
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
    provider = MiniMaxSeleniumProvider("minimax_quickstart", config)
    print(f"✅ Provider created: {provider.name}")

    # Setup output directory
    output_dir = Path("quickstart_output")
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
        print("⚠️ No reference audio found for voice cloning")
        print("   Please place a valid audio file (.wav/.mp3) in the test_output directory")
        print("   Or provide path to your reference audio file")
        return

    print(f"✅ Reference audio found: {reference_audio}")
    print(f"📊 Reference audio size: {reference_audio.stat().st_size / 1024:.1f} KB")

    # Test 1: Single voice cloning
    print("\n🧪 Test 1: Single Voice Cloning")
    print("-" * 30)

    test_text = "Xin chào, đây là MiniMax voice cloning với tiếng Việt"
    output_file = output_dir / "single_clone.wav"

    print(f"🎤 Text: {test_text}")
    print(f"📁 Output: {output_file}")

    try:
        result = provider.clone_with_metadata(test_text, reference_audio, output_file)

        if result['success'] and output_file.exists():
            file_size = output_file.stat().st_size / 1024
            print(f"✅ Success! File size: {file_size:.1f} KB")
            print(f"📊 Audio URL: {result.get('audio_url', 'None')}")
            print(f"⏱️  Estimated duration: {result.get('estimated_duration', 0):.2f}s")
        else:
            print(f"❌ Voice cloning failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Batch processing
    print("\n🧪 Test 2: Batch Processing")
    print("-" * 30)

    # Create sample text file
    text_file = output_dir / "sample_texts.txt"
    sample_texts = [
        "1\tXin chào, đây là batch processing",
        "2\tMiniMax voice cloning hoạt động tốt",
        "3\tCảm ơn bạn đã sử dụng dịch vụ",
        "4\tChúc bạn một ngày tốt lành",
        "5\tHẹn gặp lại bạn lần sau"
    ]

    text_file.write_text("\n".join(sample_texts), encoding='utf-8')
    print(f"✅ Created text file: {text_file}")

    # Load texts
    loader = TextFileLoader(text_file)
    loaded_texts = loader.load()
    print(f"📄 Loaded {len(loaded_texts)} texts")

    # Batch processing
    batch_output_dir = output_dir / "batch"
    batch_output_dir.mkdir(exist_ok=True)

    print("🎭 Starting batch voice cloning...")

    try:
        batch_result = provider.clone_batch(text_file, reference_audio, batch_output_dir)

        print("📊 Batch Results:")
        print(f"   Total texts: {batch_result.get('total_texts', 0)}")
        print(f"   Processed: {batch_result.get('processed', 0)}")
        print(f"   Failed: {batch_result.get('failed', 0)}")
        print(f"   Success rate: {batch_result.get('success_rate', 0):.1f}%")

        # Show individual results
        print("\n📋 Individual Results:")
        for result in batch_result.get('results', []):
            status = "✅" if result.get('success') else "❌"
            print(f"   {status} {result.get('id', 'unknown')}: {Path(result.get('output_file', '')).name}")
            if not result.get('success'):
                print(f"      Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Batch processing error: {e}")

    # Test 3: Provider capabilities
    print("\n🧪 Test 3: Provider Capabilities")
    print("-" * 30)

    print(f"📊 Provider Info: {provider.provider_info}")
    print(f"🎤 Supported voices: {provider.supported_voices}")
    print(f"🌍 Language: {provider.language}")
    print(f"🔊 Sample rate: {provider.sample_rate}")

    # Test 4: Using synthesize_with_metadata (which now uses clone logic)
    print("\n🧪 Test 4: Synthesize with Metadata")
    print("-" * 30)

    synth_text = "Đây là test với synthesize_with_metadata method"
    synth_output = output_dir / "synth_metadata.wav"

    print(f"🎤 Text: {synth_text}")
    print(f"📁 Output: {synth_output}")

    try:
        synth_result = provider.synthesize_with_metadata(synth_text, "cloned_voice", synth_output)

        print(f"📊 Synthesis result: {synth_result.get('success', False)}")
        print(f"📊 Error: {synth_result.get('error', 'None')}")
        if synth_result['success'] and synth_output.exists():
            print(f"✅ Success! File size: {synth_output.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Cleanup
    print("\n🧹 Cleanup")
    print("-" * 30)
    provider.cleanup()

    print(f"✅ Generated files in: {output_dir}")
    print(f"📁 Single: {output_file}")
    print(f"📁 Batch: {batch_output_dir}")

    print("\n🎉 Quick start completed!")
    print("💡 Check the notebook for more advanced examples:")
    print("   notebooks/minimax_examples.ipynb")


if __name__ == "__main__":
    main()
