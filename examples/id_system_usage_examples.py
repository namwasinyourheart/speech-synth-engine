#!/usr/bin/env python3
# ============================================================
# Usage Example: New ID System for DatasetGenerator
# Minh họa cách sử dụng hệ thống ID mới với nhiều định dạng khác nhau
# ============================================================

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.text_loaders import TextFileLoader, SimpleCSVLoader, CustomTextLoader
from speech_synth_engine.dataset.dataset_generator import DatasetGenerator


def demonstrate_text_loader_with_ids():
    """Demo TextFileLoader với hệ thống ID mới"""

    print("🎵 Demo: TextFileLoader với hệ thống ID mới")
    print("=" * 60)

    # Tạo sample data với nhiều định dạng khác nhau
    sample_dir = Path("/tmp/tts_id_demo")
    sample_dir.mkdir(exist_ok=True)

    # 1. Text file với ID format
    print("\n📄 1. Text file với ID format (1\\tQuận 1)")
    id_file = sample_dir / "vietnamese_provinces_with_id.txt"
    with open(id_file, 'w', encoding='utf-8') as f:
        f.write("1\tHồ Chí Minh\n")
        f.write("2\tHà Nội\n")
        f.write("3\tĐà Nẵng\n")
        f.write("4\tCần Thơ\n")
        f.write("5\tHải Phòng\n")

    loader = TextFileLoader(id_file)
    items = loader.load()
    print(f"✅ Loaded {len(items)} items:")
    for item_id, text in items:
        print(f"   ID {item_id}: '{text}'")

    # 2. Text file không có ID (tự tạo)
    print("\n📄 2. Text file không có ID (tự tạo ID từ line number)")
    no_id_file = sample_dir / "vietnamese_provinces_no_id.txt"
    with open(no_id_file, 'w', encoding='utf-8') as f:
        f.write("Hồ Chí Minh\n")
        f.write("Hà Nội\n")
        f.write("# Comment line\n")
        f.write("Đà Nẵng\n")
        f.write("\n")  # Empty line
        f.write("Cần Thơ\n")

    loader = TextFileLoader(no_id_file)
    items = loader.load()
    print(f"✅ Loaded {len(items)} items (empty lines skipped):")
    for item_id, text in items:
        print(f"   ID {item_id}: '{text}'")

    # 3. CSV file với id và text columns
    print("\n📊 3. CSV file với id và text columns")
    csv_file = sample_dir / "vietnamese_districts.csv"
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        f.write("id,text\n")
        f.write("1,Quận 1\n")
        f.write("2,Quận Bình Thạnh\n")
        f.write("3,Quận Ba Đình\n")
        f.write("4,Quận Tân Bình\n")

    loader = SimpleCSVLoader(csv_file)
    items = loader.load()
    print(f"✅ Loaded {len(items)} items:")
    for item_id, text in items:
        print(f"   ID {item_id}: '{text}'")

    # 4. JSON file với id và text
    print("\n📋 4. JSON file với id và text")
    json_file = sample_dir / "vietnamese_addresses.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write('''[
    {"id": "1001", "text": "123 Đường Lê Lợi"},
    {"id": "1002", "text": "456 Phố Nguyễn Huệ"},
    {"id": "1003", "text": "789 Đại lộ Võ Văn Kiệt"}
]''')

    loader = CustomTextLoader(json_file)
    items = loader.load()
    print(f"✅ Loaded {len(items)} items:")
    for item_id, text in items:
        print(f"   ID {item_id}: '{text}'")

    return sample_dir


def demonstrate_audio_generation():
    """Demo tạo audio từ các nguồn text khác nhau"""

    print("\n🎵 Demo: Tạo audio từ nhiều nguồn text")
    print("=" * 60)

    # Chuẩn bị sample data
    sample_dir = demonstrate_text_loader_with_ids()

    # Output directory
    output_dir = Path("/tmp/tts_id_demo_output")
    output_dir.mkdir(exist_ok=True)

    # 1. Từ text file với ID
    print("\n🎵 1. Từ text file với ID format")
    text_items = TextFileLoader(sample_dir / "vietnamese_provinces_with_id.txt").load()
    print(f"📝 Processing {len(text_items)} text items...")

    providers_config = {
        "gtts": {
            "sample_rate": 22050,
            "language": "vi"
        }
    }

    generator = DatasetGenerator(output_dir / "from_text_with_id", providers_config)
    summary = generator.generate_from_text_list(
        text_items=text_items,
        provider_model_voice_list=[("gtts", "default", "vi")],
        batch_size=2,
        delay_between_requests=0.5
    )

    print("✅ Generation Summary:"    print(f"   Success: {summary.successful_generations}")
    print(f"   Failed: {summary.failed_generations}")

    # Hiển thị sample kết quả
    if summary.successful_generations > 0:
        first_result = summary.results[0]
        print(f"🎵 Sample audio: {first_result.audio_path}")
        print(f"📋 Sample metadata: {first_result.metadata_path}")

    # 2. Từ CSV file
    print("\n🎵 2. Từ CSV file")
    csv_items = SimpleCSVLoader(sample_dir / "vietnamese_districts.csv").load()
    print(f"📝 Processing {len(csv_items)} CSV items...")

    generator = DatasetGenerator(output_dir / "from_csv", providers_config)
    summary = generator.generate_from_text_list(
        text_items=csv_items,
        provider_model_voice_list=[("gtts", "default", "vi")],
        batch_size=2
    )

    print("✅ Generation Summary:"    print(f"   Success: {summary.successful_generations}")
    print(f"   Failed: {summary.failed_generations}")

    # 3. Mixed sources
    print("\n🎵 3. Từ nhiều nguồn kết hợp")
    mixed_items = []

    # Từ text file không có ID
    mixed_items.extend(TextFileLoader(sample_dir / "vietnamese_provinces_no_id.txt").load())

    # Từ JSON file
    mixed_items.extend(CustomTextLoader(sample_dir / "vietnamese_addresses.json").load())

    print(f"📝 Processing {len(mixed_items)} mixed items...")

    generator = DatasetGenerator(output_dir / "mixed_sources", providers_config)
    summary = generator.generate_from_text_list(
        text_items=mixed_items,
        provider_model_voice_list=[("gtts", "default", "vi")],
        batch_size=3
    )

    print("✅ Generation Summary:"    print(f"   Success: {summary.successful_generations}")
    print(f"   Failed: {summary.failed_generations}")

    return output_dir


def demonstrate_metadata_format():
    """Demo format metadata mới"""

    print("\n📋 Demo: Format metadata.tsv mới")
    print("=" * 60)

    # Đọc sample metadata file
    metadata_file = Path("/tmp/tts_id_demo_output/from_text_with_id/gtts/default/vi/metadata.tsv")

    if metadata_file.exists():
        print(f"📖 Đọc metadata từ: {metadata_file}")
        print("\n📊 Metadata columns:")
        print("utt_id | text_id | text | audio_path | provider | model | voice | sample_rate | lang | duration | gen_date")

        print("\n📝 Sample entries:")
        with open(metadata_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:5]):  # Hiển thị 5 dòng đầu
                if i == 0:
                    print(f"Header: {line.strip()}")
                else:
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        utt_id, text_id, text, audio_path = parts[0], parts[1], parts[2], parts[3]
                        print(f"Row {i}: utt_id={utt_id}, text_id={text_id}, text='{text}', audio='{audio_path}'")

    # Demo tạo metadata trực tiếp
    print("
🏗️  Demo tạo metadata trực tiếp:"    print("metadata.tsv format:")
    print("utt_id	text_id	text	audio_path	provider	model	voice	sample_rate	lang	duration	gen_date")
    print("001	1	Hồ Chí Minh	1_Hồ_Chí_Minh.wav	gtts	default	vi	22050	vi	2.34	2025-01-18 16:15:23")
    print("002	2	Hà Nội	2_Hà_Nội.wav	gtts	default	vi	22050	vi	1.89	2025-01-18 16:15:25")


def main():
    """Main demo function"""

    print("🚀 TTS ID System Usage Examples")
    print("=" * 70)
    print("Demo các tính năng của hệ thống ID mới trong DatasetGenerator")
    print("=" * 70)

    try:
        # Demo các loại text loaders
        sample_dir = demonstrate_text_loader_with_ids()

        # Demo tạo audio từ nhiều nguồn
        output_dir = demonstrate_audio_generation()

        # Demo format metadata mới
        demonstrate_metadata_format()

        print("
🎉 Demo hoàn thành!"        print(f"📁 Sample files: {sample_dir}")
        print(f"📁 Output files: {output_dir}")
        print("
📖 Các ví dụ minh họa:"        print("   1. Text file với ID format: id\\ttext")
        print("   2. Text file không có ID: tự tạo ID từ line number")
        print("   3. CSV file: bắt buộc có columns 'id' và 'text'")
        print("   4. JSON file: có thể có 'id' và 'text' fields")
        print("   5. Metadata.tsv: có cả utt_id và text_id columns")
        print("   6. Audio generation từ nhiều nguồn kết hợp")

        return True

    except Exception as e:
        print(f"❌ Demo thất bại: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ Demo hoàn thành thành công!")
    else:
        print("\n❌ Demo gặp lỗi. Vui lòng kiểm tra lại.")
