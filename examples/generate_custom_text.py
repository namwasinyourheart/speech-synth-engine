#!/usr/bin/env python3
# ============================================================
# Generate Custom Text Audio
# Ví dụ sử dụng Enhanced Dataset Generator với text tùy chỉnh
# ============================================================

import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator, generate_vietnamese_addresses
from speech_synth_engine.dataset.text_loaders import CustomTextLoader

def setup_logging():
    """Cấu hình logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/custom_generation.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def example_1_simple_custom_text():
    """Ví dụ 1: Generate từ danh sách text đơn giản"""
    print("📝 Ví dụ 1: Generate từ danh sách text đơn giản")

    # Danh sách text mẫu
    sample_texts = [
        "Xin chào, tôi cần hỗ trợ",
        "Bạn có thể giúp tôi được không?",
        "Cảm ơn bạn rất nhiều",
        "Hẹn gặp lại bạn sau nhé",
        "Chúc bạn một ngày tốt lành"
    ]

    # Cấu hình output
    output_dir = Path("./output/custom_example_1")

    # Sử dụng convenience function
    summary = generate_vietnamese_addresses(
        output_dir=output_dir,
        texts=sample_texts,
        providers_config={
            "gtts": {
                "sample_rate": 22050,
                "language": "vi"
            }
        },
        batch_size=2,
        delay_between_requests=0.5
    )

    print(f"✅ Đã generate {summary.successful_generations} audio files")
    return summary

def example_2_custom_file():
    """Ví dụ 2: Generate từ file text tùy chỉnh"""
    print("\n📝 Ví dụ 2: Generate từ file text tùy chỉnh")

    # Tạo file text mẫu
    sample_file = Path("./sample_addresses.txt")
    sample_texts = [
        "123 Đường Lê Lợi, Quận 1, Thành phố Hồ Chí Minh",
        "456 Nguyễn Huệ, Quận Hai Bà Trưng, Hà Nội",
        "789 Trần Hưng Đạo, Quận Sơn Trà, Đà Nẵng",
        "321 Lý Thường Kiệt, Quận Ninh Kiều, Cần Thơ",
        "654 Võ Văn Kiệt, Quận Bình Thạnh, Thành phố Hồ Chí Minh"
    ]

    # Ghi file mẫu
    with open(sample_file, 'w', encoding='utf-8') as f:
        for text in sample_texts:
            f.write(text + '\n')

    # Load và generate
    loader = CustomTextLoader(sample_file)
    texts = loader.load()

    output_dir = Path("./output/custom_example_2")

    generator = EnhancedDatasetGenerator(
        output_dir=output_dir,
        providers_config={
            "gtts": {
                "sample_rate": 22050,
                "language": "vi"
            }
        }
    )

    summary = generator.generate_from_text_list(
        texts=texts,
        provider_model_voice_list=[("gtts", "default", "vi")],
        batch_size=3,
        delay_between_requests=1.0
    )

    print(f"✅ Đã generate {summary.successful_generations} địa chỉ từ file")
    return summary

def example_3_filtered_csv():
    """Ví dụ 3: Generate từ CSV với filters"""
    print("\n📝 Ví dụ 3: Generate từ CSV với filters")

    # Tạo file CSV mẫu
    csv_file = Path("./sample_data.csv")
    csv_content = """id,text,duration,category
1,Xin chào buổi sáng,2.5,greeting
2,Tôi muốn hỏi đường,3.2,question
3,Cảm ơn sự giúp đỡ,2.1,thanks
4,Bạn có khỏe không,2.8,question
5,Chúc ngủ ngon,1.9,greeting"""

    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    # Load với filters
    loader = CustomTextLoader(
        csv_file,
        text_column="text",
        filters={"category": "greeting"}  # Chỉ lấy greeting
    )
    texts = loader.load()

    print(f"📋 Texts sau khi filter: {texts}")

    output_dir = Path("./output/custom_example_3")

    generator = EnhancedDatasetGenerator(
        output_dir=output_dir,
        providers_config={
            "gtts": {
                "sample_rate": 22050,
                "language": "vi"
            }
        }
    )

    summary = generator.generate_from_text_list(
        texts=texts,
        provider_model_voice_list=[("gtts", "default", "vi")],
        batch_size=2
    )

    print(f"✅ Đã generate {summary.successful_generations} câu chào hỏi từ CSV")
    return summary

def example_4_multi_provider():
    """Ví dụ 4: Sử dụng nhiều providers cùng lúc"""
    print("\n📝 Ví dụ 4: Multi-provider generation")

    sample_texts = [
        "Đây là câu tiếng Việt đầu tiên",
        "Đây là câu tiếng Việt thứ hai",
        "Đây là câu tiếng Việt thứ ba"
    ]

    output_dir = Path("./output/custom_example_4")

    # Cấu hình nhiều providers (chỉ dùng GTTS trong ví dụ này)
    providers_config = {
        "gtts": {
            "sample_rate": 22050,
            "language": "vi"
        }
    }

    generator = EnhancedDatasetGenerator(output_dir, providers_config)

    # Có thể mở rộng để sử dụng nhiều providers thật
    provider_model_voice_list = [
        ("gtts", "default", "vi"),
        # ("azure", "neural", "vi-VN-HoaiMyNeural"),  # Khi có Azure
        # ("gemini", "default", "Kore")  # Khi có Gemini
    ]

    summary = generator.generate_from_text_list(
        texts=sample_texts,
        provider_model_voice_list=provider_model_voice_list,
        batch_size=1,
        delay_between_requests=2.0  # Delay lâu hơn cho multi-provider
    )

    print(f"✅ Multi-provider generation hoàn thành: {summary.successful_generations} files")
    return summary

def main():
    """Chạy tất cả ví dụ"""
    print("🎯 Bắt đầu các ví dụ Custom Text Generation")
    print("=" * 60)

    setup_logging()

    try:
        # Chạy các ví dụ
        results = []

        results.append(example_1_simple_custom_text())
        results.append(example_2_custom_file())
        results.append(example_3_filtered_csv())
        results.append(example_4_multi_provider())

        # Tổng kết
        print("\n" + "=" * 60)
        print("📊 TỔNG KẾT TẤT CẢ VÍ DỤ")
        print("=" * 60)

        total_successful = sum(r.successful_generations for r in results)
        total_failed = sum(r.failed_generations for r in results)
        total_duration = sum(r.total_duration for r in results)

        print(f"✅ Tổng successful generations: {total_successful}")
        print(f"❌ Tổng failed generations: {total_failed}")
        print(f"⏱️ Tổng thời gian: {total_duration:.2f} giây")

        print("\n📁 Kiểm tra kết quả tại:")
        print("   ./output/custom_example_1/")
        print("   ./output/custom_example_2/")
        print("   ./output/custom_example_3/")
        print("   ./output/custom_example_4/")

        print("\n🎉 Tất cả ví dụ hoàn thành!")
        return True

    except Exception as e:
        print(f"❌ Lỗi chạy ví dụ: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
