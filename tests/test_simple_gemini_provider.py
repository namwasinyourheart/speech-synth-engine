#!/usr/bin/env python3
# ============================================================
# Simple Gemini Provider Test
# Test đơn giản để kiểm tra Gemini provider với enhanced system
# ============================================================

import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

def setup_logging():
    """Cấu hình logging đơn giản"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_simple_gemini():
    """Test đơn giản cho Gemini provider"""
    print("🧪 Testing Simple Gemini Provider...")

    try:
        from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

        # Khởi tạo provider với config
        config = {
            "model": "gemini-2.5-flash-preview-tts",
            "sample_rate": 24000,
            "api_key": os.environ.get('GEMINI_API_KEY')  # Từ environment
        }

        provider = GeminiTTSProvider("gemini", config)

        # Kiểm tra thông tin provider
        print(f"✅ Provider name: {provider.name}")
        print(f"✅ Supported voices: {provider.supported_voices}")
        print(f"✅ Model: {provider.model}")
        print(f"✅ Sample rate: {provider.sample_rate}")

        # Test text đơn giản
        test_text = "Xin chào, đây là test Gemini TTS provider"

        # Tạo file output
        output_file = Path("test_output/simple_gemini_test.wav")

        # Synthesize
        success = provider.synthesize(test_text, "Kore", output_file)

        if success and output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Synthesize thành công: {output_file}")
            print(f"📊 File size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ Synthesize thất bại")
            return False

    except Exception as e:
        print(f"❌ Lỗi test Gemini: {e}")
        return False

def test_gemini_with_metadata():
    """Test Gemini với metadata"""
    print("\n🧪 Testing Gemini with metadata...")

    try:
        from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

        provider = GeminiTTSProvider("gemini", {
            "model": "gemini-2.5-flash-preview-tts",
            "sample_rate": 24000
        })

        test_text = "Test với metadata từ Gemini"

        output_file = Path("test_output/gemini_metadata_test.wav")
        result = provider.synthesize_with_metadata(test_text, "Kore", output_file)

        print(f"✅ Success: {result['success']}")
        print(f"📁 Output file: {result['output_file']}")
        print(f"⏱️ Duration: {result['estimated_duration']:.2f}s")
        print(f"🎤 Voice: {result['voice']}")
        print(f"🤖 Model: {result['model']}")

        return result['success']

    except Exception as e:
        print(f"❌ Lỗi test metadata: {e}")
        return False

def test_gemini_different_voices():
    """Test Gemini với các giọng khác nhau"""
    print("\n🧪 Testing Gemini với different voices...")

    try:
        from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

        provider = GeminiTTSProvider("gemini", {
            "model": "gemini-2.5-flash-preview-tts",
            "sample_rate": 24000
        })

        test_text = "Đây là test với giọng khác nhau từ Gemini"
        voices = ["Kore", "Fenrir", "Charon"]

        results = []

        for voice in voices:
            print(f"🎤 Testing voice: {voice}")

            output_file = Path(f"test_output/gemini_voice_{voice.lower()}.wav")

            try:
                success = provider.synthesize(test_text, voice, output_file)

                if success and output_file.exists():
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
    """Chạy tất cả tests đơn giản cho Gemini"""
    print("🎯 Simple Gemini Provider Tests")
    print("=" * 40)

    setup_logging()

    # Kiểm tra API key trước
    if not os.environ.get('GEMINI_API_KEY'):
        print("⚠️  CẢNH BÁO: GEMINI_API_KEY không được thiết lập!")
        print("   Các tests có thể thất bại nếu không có API key hợp lệ.")

    tests = [
        ("Basic Gemini Test", test_simple_gemini),
        ("Gemini Metadata Test", test_gemini_with_metadata),
        ("Gemini Voices Test", test_gemini_different_voices)
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
    print("📊 GEMINI TEST SUMMARY")
    print('=' * 40)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Gemini tests PASSED!")
        return True
    else:
        print("⚠️ Một số tests thất bại. Kiểm tra GEMINI_API_KEY và kết nối mạng.")
        return False

if __name__ == "__main__":
    import os
    success = main()
    sys.exit(0 if success else 1)
