#!/usr/bin/env python3
# ============================================================
# Generate Audio from Text Files
# Simple script using DatasetGenerator to create audio from txt files
# ============================================================

import os
import sys
from pathlib import Path
from typing import List

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.text_loaders import TextFileLoader
from speech_synth_engine.dataset.dataset_generator import DatasetGenerator


def generate_audio_from_text_files(
    input_files: List[Path],
    output_dir: Path,
    provider_name: str = "gtts",
    voice: str = "vi"
):
    """
    Generate audio from text files using DatasetGenerator

    Args:
        input_files: List of text file paths
        output_dir: Directory to save audio files
        provider_name: TTS provider to use ('gtts', 'gemini', etc.)
        voice: Voice to use for synthesis
    """

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all text items from input files
    all_text_items = []
    for input_file in input_files:
        try:
            loader = TextFileLoader(input_file)
            text_items = loader.load()

            # Filter out empty text items
            valid_items = [(text_id, text) for text_id, text in text_items if text.strip()]
            all_text_items.extend(valid_items)

            print(f"✅ Loaded {len(valid_items)} text items from {input_file}")

        except Exception as e:
            print(f"❌ Error loading {input_file}: {e}")
            continue

    if not all_text_items:
        print("❌ No valid text items found in input files")
        return

    print(f"\n🎵 Total text items to process: {len(all_text_items)}")

    # Configure provider
    providers_config = {
        provider_name: {
            "sample_rate": 22050 if provider_name == "gtts" else 24000,
            "language": "vi"
        }
    }

    try:
        # Initialize DatasetGenerator
        generator = DatasetGenerator(
            output_dir=output_dir,
            providers_config=providers_config
        )

        # Generate audio from text items
        summary = generator.generate_from_text_list(
            text_items=all_text_items,
            provider_model_voice_list=[(provider_name, "default", voice)],
            batch_size=10,
            delay_between_requests=0.5
        )

        # Report results
        print("\n📊 Generation Summary:")
        print(f"   ✅ Successful: {summary.successful_generations}")
        print(f"   ❌ Failed: {summary.failed_generations}")
        print(f"   📁 Audio files: {len([r for r in summary.results if r.success])}")
        print(f"   📋 Metadata files: {len([r for r in summary.results if r.success])}")

        if summary.successful_generations > 0:
            # Show sample result
            first_result = summary.results[0]
            print(f"\n🎵 Sample audio file: {first_result.audio_path}")
            print(f"📋 Sample metadata file: {first_result.metadata_path}")

        return summary

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return None


def example_usage():
    """Example usage"""

    # Define input files
    input_files = [
        Path("/home/nampv1/projects/tts/speech-synth-engine/data/provinces.txt"),
        Path("/home/nampv1/projects/tts/speech-synth-engine/data/districts.txt"),
    ]

    # Create output directory
    output_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/output/audio_from_text")

    # Generate audio
    summary = generate_audio_from_text_files(
        input_files=input_files,
        output_dir=output_dir,
        provider_name="gtts",
        voice="vi"
    )

    return summary


def create_sample_data():
    """Create sample data for testing"""

    # Create data directory
    data_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/data")
    data_dir.mkdir(exist_ok=True)

    # Create sample provinces file
    provinces_file = data_dir / "provinces.txt"
    with open(provinces_file, 'w', encoding='utf-8') as f:
        f.write("Hồ Chí Minh\n")
        f.write("Hà Nội\n")
        f.write("Đà Nẵng\n")
        f.write("Cần Thơ\n")
        f.write("Hải Phòng\n")

    # Create sample districts file
    districts_file = data_dir / "districts.txt"
    with open(districts_file, 'w', encoding='utf-8') as f:
        f.write("Quận 1\n")
        f.write("Quận Bình Thạnh\n")
        f.write("Quận Ba Đình\n")
        f.write("Quận Tân Bình\n")
        f.write("Quận Thủ Đức\n")

    print(f"✅ Created sample data files in {data_dir}")


if __name__ == "__main__":
    print("🎵 Audio Generation from Text Files")
    print("=" * 40)

    # Create sample data if it doesn't exist
    sample_files = [
        Path("/home/nampv1/projects/tts/speech-synth-engine/data/provinces.txt"),
        Path("/home/nampv1/projects/tts/speech-synth-engine/data/districts.txt"),
    ]

    if not all(f.exists() for f in sample_files):
        print("📝 Creating sample data files...")
        create_sample_data()

    print("\n🚀 Starting audio generation...")
    summary = example_usage()

    if summary and summary.successful_generations > 0:
        print("\n✨ Success! Check the output directory for generated files.")
    else:
        print("\n❌ Generation failed or no files were created.")
