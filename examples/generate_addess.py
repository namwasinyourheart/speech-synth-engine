#!/usr/bin/env python3
# ============================================================
# Generate Address Audio Dataset with ID System
# ============================================================

import os
import sys
import logging
import argparse
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatasetGenerator")
logger.setLevel(logging.INFO)

from speech_synth_engine.dataset.text_loaders import TextFileLoader


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate audio dataset from text file using TTS providers'
    )

    parser.add_argument(
        '--text_path',
        type=str,
        required=True,
        help='Path to text file to generate audio from'
    )

    parser.add_argument(
        '--output_dir',
        type=str,
        required=True,
        help='Output directory for generated audio files'
    )

    parser.add_argument(
        '--provider',
        type=str,
        default='gtts',
        choices=['gtts', 'gemini', 'vnpost'],
        help='TTS provider to use (default: gtts)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=3.0,
        help='Delay between requests in seconds (default: 3.0)'
    )

    parser.add_argument(
        '--batch_size',
        type=int,
        default=10,
        help='Batch size for processing (default: 10)'
    )

    return parser.parse_args()


def get_providers_config(provider: str) -> dict:
    """Get providers configuration based on provider type"""
    configs = {
        'gtts': {
            "gtts": {"language": "vi"}
        },
        'gemini': {
            "gemini": {
                "sample_rate": 24000,
                "model": "gemini-2.5-flash-preview-tts",
                "language": "vi"
            }
        },
        'vnpost': {
            "vnpost": {
                "sample_rate": 22050,
                "language": "vi",
                "voice": "Hà My"
            }
        }
    }

    return configs.get(provider, configs['gtts'])


def get_provider_model_voice_list(provider: str) -> list:
    """Get provider model voice list based on provider type"""
    configs = {
        'gtts': [("gtts", "default", "vi")],
        'gemini': [("gemini", "gemini-2.5-flash-preview-tts", "vi")],
        'vnpost': [("vnpost", "default", "Hà My")]
    }

    return configs.get(provider, configs['gtts'])


def main():
    """Main function"""
    args = parse_arguments()

    # Validate input file exists
    text_path = Path(args.text_path)
    if not text_path.exists():
        logger.error(f"❌ Text file not found: {text_path}")
        return 1

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"🚀 Starting generation...")
    logger.info(f"   📄 Text file: {text_path}")
    logger.info(f"   📁 Output dir: {output_dir}")
    logger.info(f"   🎵 Provider: {args.provider}")
    logger.info(f"   ⏱️ Delay: {args.delay}s")
    logger.info(f"   📦 Batch size: {args.batch_size}")

    try:
        # Load text items
        logger.info("📖 Loading text items...")
        loader = TextFileLoader(text_path)
        text_items = loader.load()

        if not text_items:
            logger.error("❌ No text items found in file")
            return 1

        logger.info(f"✅ Loaded {len(text_items)} text items")

        # Get provider configuration
        providers_config = get_providers_config(args.provider)
        provider_model_voice_list = get_provider_model_voice_list(args.provider)

        # Create generator and generate
        logger.info("🎵 Generating audio files...")
        generator = DatasetGenerator(output_dir, providers_config)

        summary = generator.generate_from_text_list(
            text_items=text_items,
            provider_model_voice_list=provider_model_voice_list,
            delay_between_requests=args.delay,
            batch_size=args.batch_size
        )

        # Report results
        logger.info("📊 Generation Summary:")
        logger.info(f"   ✅ Successful: {summary.successful_generations}")
        logger.info(f"   ⏭️ Skipped duplicates: {len([r for r in summary.results if r.skipped_duplicate])}")
        logger.info(f"   ❌ Failed: {summary.failed_generations}")
        logger.info(f"   📁 Output directory: {output_dir}")

        if summary.successful_generations > 0:
            # Show sample result
            first_result = summary.results[0]
            logger.info(f"🎵 Sample audio file: {first_result.audio_path}")
            logger.info(f"📋 Sample metadata file: {first_result.metadata_path}")

        logger.info("🎉 Generation completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"❌ Error during generation: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


# Usage Example
# python /home/nampv1/projects/asr/asr_ft/augment_data/generate_addess.py \
# --text_path /media/nampv1/hdd/data/vn_commune_district_province/raw/text/cdp_list_with_prefix.txt \
# --output_dir /media/nampv1/hdd/data/Voice-of-Address/cdp_list_with_prefix/ \
# --provider gtts \
# --delay 3.0 \
# --batch_size 10
