#!/usr/bin/env python3
# ============================================================
# Enhanced Gemini Provider Test
# Test Gemini Provider với enhanced system mới
# ============================================================

import os
import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

def setup_logging():
    """Cấu hình logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("test_output/enhanced_gemini_test.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_enhanced_gemini_provider(use_vertex_ai: bool = False):
    """
    Test Gemini Provider với enhanced system mới.
    
    Args:
        use_vertex_ai: Whether to use Vertex AI authentication
    """
    test_type = "Vertex AI" if use_vertex_ai else "API Key"
    print(f"🧪 Testing Enhanced Gemini Provider ({test_type})...")

    # Cấu hình output
    output_dir = Path(f"test_output/enhanced_gemini_{'vertex' if use_vertex_ai else 'api'}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test text tiếng Việt
    test_text = "Xin chào, đây là test với Google Gemini TTS provider mới"

    # Cấu hình Gemini provider
    providers_config = {
        "gemini": {
            "sample_rate": 24000,
            "model": "gemini-2.5-flash-preview-tts",
            "language": "vi"
        }
    }
    
    # Thêm cấu hình Vertex AI nếu cần
    if use_vertex_ai:
        providers_config["gemini"].update({
            "use_vertex_ai": True,
            "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
            "location": "us-central1"
        })

    try:
        # Khởi tạo enhanced generator
        generator = DatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config
        )

        # Test generation với Gemini
        summary = generator.generate_from_text_list(
            text_items=[("test_1", test_text)],
            provider_model_voice=("gemini", "default", "Kore"),
            batch_size=1,
            delay_between_requests=2.0  # Gemini cần thời gian xử lý
        )

        # Kiểm tra kết quả
        if summary.successful_generations > 0:
            print("✅ Enhanced Gemini Provider test THÀNH CÔNG!")

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
        print(f"❌ Lỗi khi test Enhanced Gemini Provider: {e}")
        return False

def test_gemini_multiple_voices():
    """Test Gemini với nhiều voices khác nhau"""
    print("\n🧪 Testing Gemini với multiple voices...")

    test_text = "Đây là test với nhiều giọng nói khác nhau của Gemini TTS"

    output_dir = Path("test_output/enhanced_gemini_voices")
    output_dir.mkdir(parents=True, exist_ok=True)

    providers_config = {
        "gemini": {
            "sample_rate": 24000,
            "model": "gemini-2.5-flash-preview-tts",
            "language": "vi"
        }
    }

    # Các voices có thể có của Gemini
    voices_to_test = ["Kore", "Fenrir", "Charon", "Aoede"]

    try:
        generator = DatasetGenerator(output_dir, providers_config)

        results = []
        for voice in voices_to_test:
            print(f"🎤 Testing voice: {voice}")

            summary = generator.generate_from_text_list(
                text_items=[(f"test_voice_{voice}", test_text)],
                provider_model_voice=("gemini", "default", voice),
                batch_size=1,
                delay_between_requests=3.0  # Gemini cần thời gian xử lý lâu hơn
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

def test_gemini_long_text():
    """Test Gemini với text dài"""
    print("\n🧪 Testing Gemini với long text...")

    # Text dài để test khả năng xử lý
    long_text = """
    Đây là một đoạn văn bản dài để test khả năng xử lý của Gemini TTS Provider.
    Với enhanced system mới, chúng ta có thể xử lý nhiều loại text khác nhau
    từ các nguồn khác nhau như tỉnh thành, quận huyện, hay text tùy chỉnh.
    Hệ thống mới hỗ trợ multiple providers và có khả năng batch processing
    với progress tracking và error handling tốt hơn.
    Gemini TTS có khả năng xử lý ngôn ngữ tự nhiên rất tốt với nhiều giọng nói đa dạng.
    """

    output_dir = Path("test_output/enhanced_gemini_long")
    output_dir.mkdir(parents=True, exist_ok=True)

    providers_config = {
        "gemini": {
            "sample_rate": 24000,
            "model": "gemini-2.5-flash-preview-tts",
            "language": "vi",
            "max_duration": 60.0  # Tăng max duration cho text dài
        }
    }

    try:
        generator = DatasetGenerator(output_dir, providers_config)

        summary = generator.generate_from_text_list(
            texts=[long_text.strip()],
            provider_model_voice_list=[("gemini", "default", "Kore")],
            batch_size=1,
            delay_between_requests=5.0  # Cần nhiều thời gian hơn cho text dài
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

def test_gemini_different_models():
    """Test Gemini với các models khác nhau"""
    print("\n🧪 Testing Gemini với different models...")

    test_text = "Đây là test với model khác nhau của Gemini"

    output_dir = Path("test_output/enhanced_gemini_models")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test với model mặc định
    providers_config = {
        "gemini": {
            "sample_rate": 24000,
            "model": "gemini-2.5-flash-preview-tts",
            "language": "vi"
        }
    }

    try:
        generator = DatasetGenerator(output_dir, providers_config)

        summary = generator.generate_from_text_list(
            texts=[test_text],
            provider_model_voice_list=[("gemini", "gemini-2.5-flash-preview-tts", "Kore")],
            batch_size=1,
            delay_between_requests=3.0
        )

        if summary.successful_generations > 0:
            result = summary.results[0]
            print("✅ Gemini model test THÀNH CÔNG!")
            print(f"📁 Audio file: {result.audio_path}")
            print(f"🤖 Model: {result.metadata_path}")
            return True
        else:
            print(f"❌ Model test thất bại: {summary.errors}")
            return False

    except Exception as e:
        print(f"❌ Lỗi test different models: {e}")
        return False

def test_enhanced_gemini_provider(use_vertex_ai=False):
    """Test Gemini với enhanced system"""
    print("\n🧪 Testing Enhanced Gemini Provider...")

    test_text = "Đây là test với enhanced system của Gemini TTS Provider"

    output_dir = Path("test_output/enhanced_gemini")
    output_dir.mkdir(parents=True, exist_ok=True)

    providers_config = {
        "gemini": {
            "sample_rate": 24000,
            "model": "gemini-2.5-flash-preview-tts",
            "language": "vi"
        }
    }

    try:
        # Khởi tạo enhanced generator
        generator = DatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config,
            use_vertex_ai=use_vertex_ai
        )

        # Test generation với Gemini
        summary = generator.generate_from_text_list(
            text_items=[("test_1", test_text)],
            provider_model_voice=("gemini", "default", "Kore"),
            batch_size=1,
            delay_between_requests=2.0  # Gemini cần thời gian xử lý
        )

        # Kiểm tra kết quả
        if summary.successful_generations > 0:
            print("✅ Enhanced Gemini Provider test THÀNH CÔNG!")

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
        print(f"❌ Lỗi khi test Enhanced Gemini Provider: {e}")
        return False

def main():
    """Chạy tất cả tests cho Gemini enhanced"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    results = []
    all_passed = True
    
    # Test với API Key
    test_name_api = "Gemini API Key Test"
    try:
        logger.info("🚀 Bắt đầu test Gemini Provider với API Key...")
        success = test_enhanced_gemini_provider(use_vertex_ai=False)
        results.append((test_name_api, success))
        
        if success:
            logger.info("✅ Test Gemini Provider với API Key thành công!")
            print(f"✅ {test_name_api}: PASSED")
        else:
            logger.error("❌ Test Gemini Provider với API Key thất bại!")
            print(f"❌ {test_name_api}: FAILED")
            all_passed = False
    except Exception as e:
        logger.error(f"❌ Lỗi khi test với API Key: {e}", exc_info=True)
        print(f"💥 {test_name_api}: ERROR - {e}")
        results.append((test_name_api, False))
        all_passed = False
    
    # Test với Vertex AI nếu có thông tin xác thực
    test_name_vertex = "Gemini Vertex AI Test"
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.getenv("GOOGLE_CLOUD_PROJECT"):
        try:
            logger.info("\n🚀 Bắt đầu test Gemini Provider với Vertex AI...")
            success = test_enhanced_gemini_provider(use_vertex_ai=True)
            results.append((test_name_vertex, success))
            
            if success:
                logger.info("✅ Test Gemini Provider với Vertex AI thành công!")
                print(f"✅ {test_name_vertex}: PASSED")
            else:
                logger.error("❌ Test Gemini Provider với Vertex AI thất bại!")
                print(f"❌ {test_name_vertex}: FAILED")
                all_passed = False
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi test với Vertex AI: {e}", exc_info=True)
            print(f"💥 {test_name_vertex}: ERROR - {e}")
            results.append((test_name_vertex, False))
            all_passed = False
    else:
        logger.warning("\n⚠️ Bỏ qua test Vertex AI do thiếu thông tin xác thực")
        logger.warning("Vui lòng đặt biến môi trường GOOGLE_APPLICATION_CREDENTIALS và GOOGLE_CLOUD_PROJECT")
        print("⚠️ Skipping Vertex AI tests - Missing authentication")
    
    # Chạy các test khác
    test_functions = [
        ("Multiple Voices Test", test_gemini_multiple_voices),
        ("Long Text Test", test_gemini_long_text),
        ("Different Models Test", test_gemini_different_models)
    ]
    
    for test_name, test_func in test_functions:
        try:
            logger.info(f"\n🚀 Bắt đầu test: {test_name}")
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name} thành công!")
                print(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name} thất bại!")
                print(f"❌ {test_name}: FAILED")
                all_passed = False
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi chạy {test_name}: {e}", exc_info=True)
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
            all_passed = False
    
    # Tổng kết
    print(f"\n{'=' * 50}")
    print("📊 GEMINI ENHANCED TEST SUMMARY")
    print('=' * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if all_passed and passed == total:
        print("🎉 Tất cả tests đều PASSED! Gemini hoạt động tốt với enhanced system.")
    else:
        print("\n⚠️ Một số tests thất bại. Vui lòng kiểm tra log để biết chi tiết.")
        if not (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.getenv("GOOGLE_CLOUD_PROJECT")):
            print("⚠️ Lưu ý: Các test Vertex AI đã bị bỏ qua do thiếu thông tin xác thực.")
            print("   Vui lòng đặt biến môi trường GOOGLE_APPLICATION_CREDENTIALS và GOOGLE_CLOUD_PROJECT")
    
    return all_passed and (passed == total)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
