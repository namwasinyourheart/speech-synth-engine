#!/usr/bin/env python3
# ============================================================
# Simple GTTS Provider Test
# Test đơn giản để kiểm tra GTTS provider với enhanced system
# ============================================================

import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

def setup_logging():
    """Cấu hình logging đơn giản"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_simple_gtts():
    """Test đơn giản cho GTTS provider"""
    print("🧪 Testing Simple GTTS Provider...")

    try:
        from speech_synth_engine.providers.gtts_provider import GTTSProvider

        # Khởi tạo provider với config
        config = {"language": "vi", "sample_rate": 22050}
        provider = GTTSProvider("gtts", config)

        # Kiểm tra thông tin provider
        print(f"✅ Provider name: {provider.name}")
        print(f"✅ Supported voices: {provider.supported_voices}")
        print(f"✅ Language: {provider.lang}")
        print(f"✅ Sample rate: {provider.sample_rate}")

        # Test text đơn giản
        test_text = "Xin chào, đây là test GTTS provider"

        # Tạo file output
        output_file = Path("test_output/simple_gtts_test.wav")

        # Synthesize
        success = provider.synthesize(test_text, "vi", output_file)

        if success and output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Synthesize thành công: {output_file}")
            print(f"📊 File size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ Synthesize thất bại")
            return False

    except Exception as e:
        print(f"❌ Lỗi test GTTS: {e}")
        return False

def test_gtts_with_metadata():
    """Test GTTS với metadata"""
    print("\n🧪 Testing GTTS with metadata...")

    try:
        from speech_synth_engine.providers.gtts_provider import GTTSProvider

        provider = GTTSProvider("gtts", {"language": "vi"})
        test_text = "Test với metadata"

        output_file = Path("test_output/gtts_metadata_test.wav")
        result = provider.synthesize_with_metadata(test_text, "vi", output_file)

        print(f"✅ Success: {result['success']}")
        print(f"📁 Output file: {result['output_file']}")
        print(f"⏱️ Duration: {result['estimated_duration']:.2f}s")
        print(f"📊 Provider: {result['provider']}")

        return result['success']

    except Exception as e:
        print(f"❌ Lỗi test metadata: {e}")
        return False

def main():
    """Chạy tất cả tests đơn giản cho GTTS"""
    print("🎯 Simple GTTS Provider Tests")
    print("=" * 40)

    setup_logging()

    tests = [
        ("Basic GTTS Test", test_simple_gtts),
        ("GTTS Metadata Test", test_gtts_with_metadata)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running: {test_name}")
        print('-' * 40)

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

    # Tổng kết
    print(f"\n{'=' * 40}")
    print("📊 GTTS TEST SUMMARY")
    print('=' * 40)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All GTTS tests PASSED!")
        return True
    else:
        print("⚠️ Một số tests thất bại.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
