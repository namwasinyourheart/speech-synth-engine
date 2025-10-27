#!/usr/bin/env python3
# ============================================================
# GTTS Provider Test
# Test GTTS Provider
# ============================================================

import os
import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("tests/test_output/gtts_test.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_gtts_provider():
    """
    Test GTTS Provider.
    """
    print("🧪 Testing GTTS Provider...")

    # Configure output
    output_dir = Path("tests/test_output/gtts")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test text tiếng Việt from test origin
    test_text = "Xã Cư Dliê M'nông Huyện Cư M'gar Tỉnh Đắk Lắk"

    # Configure provider
    providers_config = {
        "gtts": {
            "sample_rate": 22050,
            "language": "vi",
            "chars_per_second": 12
        }
    }

    try:
        # Initialize generator
        generator = DatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config
        )

        # Test generation
        summary = generator.generate_from_text_list(
            texts=[test_text],
            provider_model_voice_list=[("gtts", "default", "vi")],
            batch_size=1,
            delay_between_requests=0.5
        )

        # Check result
        if summary.successful_generations > 0:
            print("✅ GTTS Provider test SUCCESS!")

            # Display information of created file
            result = summary.results[0]
            print(f"📁 Audio file: {result.audio_path}")
            print(f"📋 Metadata file: {result.metadata_path}")
            # print(f"⏱️ Duration: {result.duration:.2f}s")

            # Check if file exists
            if result.audio_path.exists():
                file_size = result.audio_path.stat().st_size
                # print(f"📊 File size: {file_size / 1024:.2f} KB")

            return True
        else:
            print(f"❌ Test failed: {summary.errors}")
            return False

    except Exception as e:
        print(f"❌ Error when testing GTTS Provider: {e}")
        return False

def test_multiple_texts():
    """Test with multiple texts"""
    print("\n🧪 Testing with multiple texts...")

    test_texts = [
        "Xin chào, đây là test đầu tiên",
        "Đây là test thứ hai với enhanced system",
        "Test cuối cùng để kiểm tra hoạt động"
    ]

    output_dir = Path("tests/test_output/gtts_multiple")
    output_dir.mkdir(parents=True, exist_ok=True)

    providers_config = {
        "gtts": {
            "sample_rate": 22050,
            "language": "vi"
        }
    }

    try:
        generator = DatasetGenerator(output_dir, providers_config)

        summary = generator.generate_from_text_list(
            texts=test_texts,
            provider_model_voice_list=[("gtts", "default", "vi")],
            batch_size=2,
            delay_between_requests=1.0
        )

        print(f"✅ Multiple texts test: {summary.successful_generations}/{summary.total_texts} successful")
        return summary.successful_generations == len(test_texts)

    except Exception as e:
        print(f"❌ Error when testing multiple texts: {e}")
        return False

def test_directory_structure():
    """Test directory structure and metadata"""
    print("\n🧪 Testing directory structure...")

    output_dir = Path("tests/test_output/gtts_structure")
    providers_config = {"gtts": {"sample_rate": 22050}}

    try:
        generator = DatasetGenerator(output_dir, providers_config)

        # Test create directory structure
        wav_dir, metadata_file = generator.directory_manager.create_provider_structure(
            "gtts", "default", "vi"
        )

        print(f"✅ Directory structure created:")
        print(f"   WAV dir: {wav_dir}")
        print(f"   Metadata: {metadata_file}")

        # Test add metadata
        test_text = "Test directory structure"
        audio_path = wav_dir / "test_001_test_directory_structure.wav"

        success = generator.directory_manager.add_metadata_entry(
            metadata_file=metadata_file,
            text=test_text,
            audio_path=audio_path,
            provider="gtts",
            model="default",
            voice="vi"
        )

        if success:
            print("✅ Metadata entry added successfully")
            return True
        else:
            print("❌ Error adding metadata entry")
            return False

    except Exception as e:
        print(f"❌ Error when testing directory structure: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 GTTS Provider Test Suite")
    print("=" * 50)

    setup_logging()

    tests = [
        # ("Enhanced GTTS Provider", test_enhanced_gtts_provider),
        ("Multiple Texts", test_multiple_texts),
        # ("Directory Structure", test_directory_structure)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 50}")
        print(f"Running: {test_name}")
        print('=' * 50)

        try:
            success = test_func()
            results.append((test_name, success))

            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")

        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Test Summary
    print(f"\n{'=' * 50}")
    print("📊 TEST SUMMARY")
    print('=' * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests PASSED!")
        return True
    else:
        print("⚠️ Some tests failed. Need to check again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
