#!/usr/bin/env python3
# ============================================================
# Enhanced VNPost Provider Test
# Test VNPost Provider với enhanced system mới
# ============================================================

import os
import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
# sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

def setup_logging():
    """Cấu hình logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("test_output/enhanced_vnpost_test.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_enhanced_vnpost_provider():
    """
    Test VNPost Provider với enhanced system mới.
    """
    print("🧪 Testing Enhanced VNPost Provider...")

    # Cấu hình output
    output_dir = Path("test_output/enhanced_vnpost")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test text tiếng Việt từ test gốc
    test_text = "Xin chào, đây là giọng nói tổng hợp được sinh ra từ VnPost TTS"

    # Cấu hình VNPost provider
    providers_config = {
        "vnpost": {
            "sample_rate": 22050,
            "language": "vi",
            "chars_per_second": 14,
            "voice": "Hà My"
        }
    }

    try:
        # Khởi tạo enhanced generator
        generator = EnhancedDatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config
        )

        # Test generation với VNPost
        summary = generator.generate_from_text_list(
            texts=[test_text],
            provider_model_voice_list=[("vnpost", "default", "Hà My")],
            batch_size=1,
            delay_between_requests=1.0  # VNPost có thể cần thời gian xử lý lâu hơn
        )

        # Kiểm tra kết quả
        if summary.successful_generations > 0:
            print("✅ Enhanced VNPost Provider test THÀNH CÔNG!")

            # Hiển thị thông tin file được tạo
            result = summary.results[0]
            print(f"📁 Audio file: {result.audio_path}")
            print(f"📋 Metadata file: {result.metadata_path}")
            print(f"⏱️ Duration: {result.duration:.2f}s")

            # Kiểm tra file tồn tại
            if result.audio_path.exists():
                file_size = result.audio_path.stat().st_size
                print(f"📊 File size: {file_size / 1024:.2f} KB")

            return True
        else:
            print(f"❌ Test thất bại: {summary.errors}")
            return False

    except Exception as e:
        print(f"❌ Lỗi khi test Enhanced VNPost Provider: {e}")
        return False

def test_vnpost_multiple_voices():
    """Test VNPost với nhiều voices khác nhau"""
    print("\n🧪 Testing VNPost với multiple voices...")

    test_text = "Đây là test với nhiều giọng nói khác nhau của VNPost"

    output_dir = Path("test_output/enhanced_vnpost_voices")
    output_dir.mkdir(parents=True, exist_ok=True)

    providers_config = {
        "vnpost": {
            "sample_rate": 22050,
            "language": "vi",
            "chars_per_second": 14
        }
    }

    # Các voices có thể có của VNPost
    voices_to_test = ["Hà My", "Lan Chi", "Bảo Khang"]

    try:
        generator = EnhancedDatasetGenerator(output_dir, providers_config)

        results = []
        for voice in voices_to_test:
            print(f"🎤 Testing voice: {voice}")

            summary = generator.generate_from_text_list(
                texts=[test_text],
                provider_model_voice_list=[("vnpost", "default", voice)],
                batch_size=1,
                delay_between_requests=2.0  # VNPost cần thời gian xử lý
            )

            if summary.successful_generations > 0:
                result = summary.results[0]
                results.append({
                    'voice': voice,
                    'audio_path': result.audio_path,
                    'duration': result.duration
                })
                print(f"✅ Voice {voice}: OK")
            else:
                print(f"❌ Voice {voice}: FAILED")

        successful_voices = len(results)
        print(f"\n📊 Kết quả: {successful_voices}/{len(voices_to_test)} voices thành công")

        if successful_voices > 0:
            print("🎵 Các voice thành công:")
            for result in results:
                print(f"   🎤 {result['voice']}: {result['audio_path']} ({result['duration']:.2f}s)")

        return successful_voices > 0

    except Exception as e:
        print(f"❌ Lỗi test multiple voices: {e}")
        return False

def test_vnpost_long_text():
    """Test VNPost với text dài"""
    print("\n🧪 Testing VNPost với long text...")

    # Text dài để test khả năng xử lý
    long_text = """
    Đây là một đoạn văn bản dài để test khả năng xử lý của VNPost TTS Provider.
    Với enhanced system mới, chúng ta có thể xử lý nhiều loại text khác nhau
    từ các nguồn khác nhau như tỉnh thành, quận huyện, hay text tùy chỉnh.
    Hệ thống mới hỗ trợ multiple providers và có khả năng batch processing
    với progress tracking và error handling tốt hơn.
    """

    output_dir = Path("test_output/enhanced_vnpost_long")
    output_dir.mkdir(parents=True, exist_ok=True)

    providers_config = {
        "vnpost": {
            "sample_rate": 22050,
            "language": "vi",
            "chars_per_second": 14,
            "max_duration": 30.0  # Tăng max duration cho text dài
        }
    }

    try:
        generator = EnhancedDatasetGenerator(output_dir, providers_config)

        summary = generator.generate_from_text_list(
            texts=[long_text.strip()],
            provider_model_voice_list=[("vnpost", "default", "Hà My")],
            batch_size=1,
            delay_between_requests=3.0  # Cần nhiều thời gian hơn cho text dài
        )

        if summary.successful_generations > 0:
            result = summary.results[0]
            print("✅ Long text test THÀNH CÔNG!")
            print(f"📁 Audio file: {result.audio_path}")
            print(f"⏱️ Duration: {result.duration:.2f}s")

            if result.audio_path.exists():
                file_size = result.audio_path.stat().st_size
                print(f"📊 File size: {file_size / 1024:.2f} KB")
                print(f"📏 Text length: {len(long_text)} characters")

            return True
        else:
            print(f"❌ Long text test thất bại: {summary.errors}")
            return False

    except Exception as e:
        print(f"❌ Lỗi test long text: {e}")
        return False

def main():
    """Chạy tất cả tests cho VNPost"""
    print("🎯 Enhanced VNPost Provider Test Suite")
    print("=" * 50)

    setup_logging()

    tests = [
        # ("Enhanced VNPost Provider", test_enhanced_vnpost_provider),
        ("Multiple Voices", test_vnpost_multiple_voices),
        # ("Long Text", test_vnpost_long_text)
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

    # Tổng kết
    print(f"\n{'=' * 50}")
    print("📊 VNPOST TEST SUMMARY")
    print('=' * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All VNPost tests PASSED! VNPost enhanced system hoạt động tốt.")
        return True
    else:
        print("⚠️ Một số VNPost tests thất bại. VNPost provider có thể cần cấu hình đặc biệt.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
