import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

def test_dataset_generator():
    """
    Test DatasetGenerator với GeminiTTSProvider.
    """
    # Khởi tạo TTS provider
    tts_provider = GeminiTTSProvider()

    # Tạo thư mục output cố định
    output_dir = Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/audio")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Khởi tạo DatasetGenerator
    generator = DatasetGenerator(
        output_dir=output_dir,
        tts_provider=tts_provider
    )

    # Test corpus
    text_corpus = [
        'Tỉnh An Giang',
        'Tỉnh Bà Rịa - Vũng Tàu',
        # 'Tỉnh Bắc Giang',
        # 'Tỉnh Bắc Kạn',
        # 'Tỉnh Bạc Liêu',
        # 'Tỉnh Bắc Ninh',
        # 'Tỉnh Bến Tre',
        # 'Tỉnh Bình Định',
        # 'Tỉnh Bình Dương',
        # 'Tỉnh Bình Phước',
        # 'Tỉnh Bình Thuận',
        # 'Tỉnh Cà Mau',
        # 'Thành phố Cần Thơ',
        # 'Tỉnh Cao Bằng',
        # 'Thành phố Đà Nẵng',
        # 'Tỉnh Đắk Lắk',
    ]

    # Test voices
    voices = [
        "Kore", 
        # "Fenrir", 
        # "Aoede"
    ]

    # Generate dataset
    try:
        generator.generate(text_corpus, voices)
        print(f"✅ Successfully generated {len(text_corpus) * len(voices)} audio files")
        print(f"📁 Output directory: {output_dir}")

        # Kiểm tra metadata
        print(f"📊 Generated {len(generator.metadata)} metadata entries")

        # Kiểm tra file được tạo
        audio_files = list(output_dir.glob("*.wav"))
        print(f"🎵 Found {len(audio_files)} WAV files")

        for metadata in generator.metadata[:3]:  # Show first 3 entries
            print(f"  - {metadata['file']}: '{metadata['text'][:30]}...' (voice: {metadata['voice']})")

        return True

    except Exception as e:
        print(f"❌ Error generating dataset: {e}")
        return False

if __name__ == "__main__":
    success = test_dataset_generator()
    if success:
        print("\n🎉 Dataset generation test completed successfully!")
    else:
        print("\n💥 Dataset generation test failed!")
        sys.exit(1)
