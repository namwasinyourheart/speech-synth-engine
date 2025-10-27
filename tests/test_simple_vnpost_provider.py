#!/usr/bin/env python3
# ============================================================
# Simple VNPost Provider Test
# Test đơn giản để kiểm tra VNPost provider với enhanced system
# ============================================================

import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

def setup_logging():
    """Cấu hình logging đơn giản"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_simple_vnpost():
    """Test đơn giản cho VNPost provider"""
    print("🧪 Testing Simple VNPost Provider...")

    try:
        from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider

        # Khởi tạo provider (interface cũ)
        provider = VnPostTTSProvider()

        # Kiểm tra thông tin cơ bản
        print(f"✅ Provider name: {provider.name}")
        print(f"✅ API URL: {provider.api_url}")

        # Test text đơn giản
        test_text = "Xin chào, đây là test VNPost provider"

        # Tạo file output
        output_file = Path("test_output/simple_vnpost_test.wav")

        # Synthesize
        provider.synthesize(test_text, "Hà My", output_file)

        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Synthesize thành công: {output_file}")
            print(f"📊 File size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ Synthesize thất bại")
            return False

    except Exception as e:
        print(f"❌ Lỗi test VNPost: {e}")
        return False

def test_vnpost_different_voices():
    """Test VNPost với các giọng khác nhau"""
    print("\n🧪 Testing VNPost với different voices...")

    try:
        from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider

        provider = VnPostTTSProvider()
        test_text = "Đây là test với giọng khác nhau"

        voices = ["Hà My", "Lan Anh", "Minh Quân"]

        results = []

        for voice in voices:
            print(f"🎤 Testing voice: {voice}")

            output_file = Path(f"test_output/vnpost_voice_{voice.replace(' ', '_').lower()}.wav")

            try:
                provider.synthesize(test_text, voice, output_file)

                if output_file.exists():
                    file_size = output_file.stat().st_size
                    results.append((voice, True, file_size))
                    print(f"✅ Voice {voice}: OK ({file_size/1024:.1f} KB)")
                else:
                    results.append((voice, False, 0))
                    print(f"❌ Voice {voice}: FAILED")

            except Exception as e:
                results.append((voice, False, 0))
                print(f"❌ Voice {voice}: ERROR - {e}")

        successful = sum(1 for _, success, _ in results if success)
        print(f"\n📊 Kết quả: {successful}/{len(voices)} voices thành công")

        return successful > 0

    except Exception as e:
        print(f"❌ Lỗi test voices: {e}")
        return False

def main():
    """Chạy tất cả tests đơn giản cho VNPost"""
    print("🎯 Simple VNPost Provider Tests")
    print("=" * 40)

    setup_logging()

    tests = [
        ("Basic VNPost Test", test_simple_vnpost),
        ("VNPost Voices Test", test_vnpost_different_voices)
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
    print("📊 VNPOST TEST SUMMARY")
    print('=' * 40)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All VNPost tests PASSED!")
        return True
    else:
        print("⚠️ Một số tests thất bại.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
