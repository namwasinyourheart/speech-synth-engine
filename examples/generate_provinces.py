#!/usr/bin/env python3
# ============================================================
# Generate Vietnamese Provinces Audio
# Ví dụ sử dụng Enhanced Dataset Generator để tạo audio cho tỉnh thành
# ============================================================

import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import EnhancedDatasetGenerator
from speech_synth_engine.dataset.text_loaders import TextLoaderFactory

def setup_logging():
    """Cấu hình logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/province_generation.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function để generate audio cho tỉnh thành"""

    # Cấu hình
    output_dir = Path("/media/nampv1/hdd/data/vn_commune_district_province/tts_generated")
    province_file = Path("/media/nampv1/hdd/data/vn_commune_district_province/raw/text/province_list_with_prefix.txt")

    # Setup logging
    setup_logging()

    print("🎯 Bắt đầu generate audio cho tỉnh thành Việt Nam")
    print(f"📁 Output directory: {output_dir}")
    print(f"📖 Province file: {province_file}")

    try:
        # Bước 1: Load danh sách tỉnh
        print("\n📖 Đang load danh sách tỉnh...")
        province_loader = TextLoaderFactory.create_loader(province_file, "province")
        provinces = province_loader.load()

        print(f"✅ Đã load {len(provinces)} tỉnh thành")

        # Hiển thị một vài ví dụ
        print("📋 Ví dụ một vài tỉnh:")
        for i, province in enumerate(provinces[:5]):
            print(f"   {i+1:2d}. {province}")
        if len(provinces) > 5:
            print(f"   ... và {len(provinces) - 5} tỉnh khác")

        # Bước 2: Cấu hình providers
        providers_config = {
            "gtts": {
                "sample_rate": 22050,
                "language": "vi",
                "chars_per_second": 12
            }
        }

        # Bước 3: Khởi tạo generator
        print("\n🔧 Đang khởi tạo TTS generator...")
        generator = DatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config
        )

        # Bước 4: Cấu hình generation
        provider_model_voice_list = [
            ("gtts", "default", "vi")
        ]

        generation_config = {
            "batch_size": 5,  # Xử lý 5 tỉnh mỗi batch
            "delay_between_requests": 1.0,  # Delay 1s giữa các requests
            "continue_on_error": True
        }

        # Bước 5: Thực hiện generation
        print("\n🚀 Bắt đầu generation...")
        print(f"📊 Tổng số tỉnh cần xử lý: {len(provinces)}")

        summary = generator.generate_from_text_list(
            texts=provinces,
            provider_model_voice_list=provider_model_voice_list,
            **generation_config
        )

        # Bước 6: Hiển thị kết quả
        print("\n📊 KẾT QUẢ GENERATION:")
        print(f"   ✅ Thành công: {summary.successful_generations}/{summary.total_texts}")
        print(f"   ❌ Thất bại: {summary.failed_generations}")
        print(f"   ⏱️ Thời gian: {summary.total_duration:.2f} giây")

        if summary.errors:
            print(f"\n⚠️ Có {len(summary.errors)} lỗi:")
            for i, error in enumerate(summary.errors[:3], 1):
                print(f"   {i}. {error}")
            if len(summary.errors) > 3:
                print(f"   ... và {len(summary.errors) - 3} lỗi khác")

        # Bước 7: Hiển thị thống kê cấu trúc
        print("\n📁 THỐNG KÊ CẤU TRÚC:")
        stats = generator.get_generation_stats()

        for provider_info in stats.get('providers', []):
            provider_name = provider_info['name']
            print(f"\n🏛️ Provider: {provider_name}")

            for model_info in provider_info.get('models', []):
                model_name = model_info['name']
                print(f"   📦 Model: {model_name}")

                for voice_info in model_info.get('voices', []):
                    voice_name = voice_info['name']
                    audio_count = voice_info['audio_files']
                    metadata_count = voice_info['metadata_entries']
                    print(f"      🎤 Voice: {voice_name}")
                    print(f"         📊 Audio files: {audio_count}")
                    print(f"         📋 Metadata entries: {metadata_count}")

        # Bước 8: Validate kết quả
        print("\n🔍 Đang validate kết quả...")
        validation_result = generator.validate_generation()

        if validation_result.get('total_audio_files', 0) > 0:
            print(f"✅ Validation thành công: {validation_result['total_audio_files']} files audio")
        else:
            print("⚠️ Cần kiểm tra lại kết quả generation")

        print("\n🎉 Hoàn thành generation tỉnh thành!")
        print(f"📁 Kiểm tra kết quả tại: {output_dir}")

        return True

    except Exception as e:
        print(f"❌ Lỗi trong quá trình generation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
