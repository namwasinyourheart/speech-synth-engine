import os
import sys
import logging
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.dataset_generator import DatasetGenerator


output_dir = Path("test_output/test_generator_gemini_1")
output_dir.mkdir(parents=True, exist_ok=True)

# Test text in Vietnamese
test_text = "Xin chào, đây là test với Gemini TTS provider"
test_texts = [
    ('0108245608_2', 'số sáu mươi sáu, đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội'),
    ('0108235818', 'số ba trăm chín mươi tám đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội')
]

test_texts = [
    ('0109720214', 'xóm hai, xã phú phương, huyện ba vì, thành phố hà nội'),
    ('0109675882', 'xóm mười, thôn phương khê, xã phú phương, huyện ba vì, thành phố hà nội'),
#     ('0109543565', 'xóm mười, xã phú phương, huyện ba vì, thành phố hà nội'),
#     ('0108521223', 'xóm mười, thôn phương khê, xã phú phương, huyện ba vì, thành phố hà nội'),
#     ('0108165818', 'xóm hai, thôn phương châu, xã phú phương, huyện ba vì, thành phố hà nội'),
#     ('0107155895', 'phương châu, xã phú phương, huyện ba vì, hà nội'),
#     ('0106918456', 'phương khê, xã phú phương, huyện ba vì, hà nội'),
#     ('0106702665', 'thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     ('0106688805', 'xóm bảy, thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     ('0106540809', 'thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     ('0106323882', 'xóm sáu, xã phú phương, huyện ba vì, hà nội'),
#     ('0105972877', 'xóm mười hai, thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     ('0105915251', 'xóm hai, thôn phương châu, xã phú phương, huyện ba vì, hà nội'),
#     ('0105810587', 'phú phương xã phú phương, huyện ba vì, hà nội'),
#     ('0105760135', 'xóm tám, xã phú phương, huyện ba vì, hà nội'),
#     ('0104016244', 'phú phương ba vì xã phú phương, huyện ba vì, hà nội')
]

# Configure Gemini provider
providers_config = {
    "gemini": {
    }
}

providers_config = {
    "gemini": {
    'use_vertex_ai': True,
    'credentials_path': '/home/nampv1/projects/tts/speech-synth-engine/notebooks/learn-gcp-first-project-202506-fe9cece37e90.json',
    'project_id': 'learn-gcp-first-project-202506',
    'location': 'global',  # Optional, defaults to us-central1
    # 'model': 'gemini-2.5-flash-preview-tts',
    'sample_rate': 24000
}
}

try:
    # Initialize generator
    generator = DatasetGenerator(
        output_dir=output_dir,
        providers_config=providers_config
    )

    # Test generation with ElevenLabs
    summary = generator.generate_from_text_list(
        text_items=test_texts,
        provider_model_voice=("gemini", "gemini-2.5-flash-preview-tts", "Zephyr"),
        batch_size=1,
        delay_between_requests=2.0
    )

    # Check results
    if summary.successful_generations > 0:
        result = summary.results[0]
        print("✅ ElevenLabs Provider test SUCCESSFUL!")
        print(f"📁 Audio file: {result.audio_path}")
        print(f"⏱️ Duration: {result.duration:.2f}s")
        
        if result.audio_path.exists():
            file_size = result.audio_path.stat().st_size
            print(f"📊 File size: {file_size / 1024:.2f} KB")

    else:
        print(f"❌ Test failed: {summary.errors}")


except Exception as e:
    print(f"❌ Error testing ElevenLabs Provider: {e}")
