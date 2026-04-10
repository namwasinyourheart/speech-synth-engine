import os
import sys

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from pathlib import Path
from datetime import datetime
from speech_synth_engine.schemas.provider import ProviderConfig, ReplicatedVoiceConfig, AudioConfig, CredentialsConfig
from speech_synth_engine.schemas.generation import VoiceCloningConfig
from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

from rich import print

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Test texts in Vietnamese
test_texts = [
    ('tts_001', 'Bản tin sáng ngày 12 tháng 3 năm 2026 cho biết nhiệt độ tại Hà Nội dao động từ 22 đến 28 độ C, độ ẩm khoảng 75 phần trăm và có khả năng mưa nhẹ vào buổi chiều.'),
    ('tts_002', 'Theo báo cáo công bố ngày 10 tháng 3 năm 2026, GDP quý một ước tính tăng khoảng 6,2 phần trăm so với cùng kỳ năm 2025.'),
    # ('tts_003', 'Giá vàng SJC sáng nay ở mức khoảng 81 triệu đồng một lượng, tăng gần 500 nghìn đồng so với phiên giao dịch ngày hôm qua.'),
    # ('tts_004', 'Tính đến ngày 1 tháng 3 năm 2026, Việt Nam đã đón hơn 3,5 triệu lượt khách du lịch quốc tế.'),
]

# Alternative: Load from file
from speech_synth_engine.dataset.utils import load_list_from_txt, make_text_items, save_items_to_tsv_txt

# text_path = "/home/nampv1/projects/tts/speech-synth-engine/examples/example_data/provinces.txt"
# texts = load_list_from_txt(text_path)
# test_texts = make_text_items(texts, method="incremental", prefix=None, pad=5, deduplicate=True, keep="first")


# Build VoiceCloningConfig for Xiaomi
# Note: Xiaomi provider doesn't need credentials (no API key required)
credentials_cfg = CredentialsConfig()  # Minimal credentials for pydantic validation

provider_config = ProviderConfig(
    name="xiaomi",
    models=["OmniVoice"],
    default_model="OmniVoice",
    credentials=credentials_cfg,
)

# Voice cloning configuration with reference audio (used for reference_audio only)
replicated_voice = ReplicatedVoiceConfig(
    reference_audio="/media/nampv1/hdd/data/VoiceGarden/elevenlabs/15_female_north_young_story_foxi_10s.mp3",
    reference_text=None,  # Will be auto-transcribed using VNPost STT API
    language="vi"
)

# Optional audio configuration (Xiaomi returns WAV by default)
audio_config = AudioConfig(
    channel=1,
    sample_rate=24000,
    container="wav",
)

# VoiceCloningConfig for voice cloning with Xiaomi
generation_config = VoiceCloningConfig(
    model="OmniVoice",
    voice_config=replicated_voice,
    audio_config=audio_config
)

import time
current_time = time.strftime("%Y%m%d_%H%M%S")

# Use DatasetGenerator main flow
output_dir = f"/home/nampv1/projects/tts/speech-synth-engine/try/try_output/data_generator/test_generator_xiaomi/{current_time}"

generator = DatasetGenerator(
    output_dir=output_dir,
    verbose=True
)

# Generate dataset using voice cloning
summary = generator.generate_from_configs(
    text_items=test_texts,
    provider_config=provider_config,
    generation_config=generation_config,
    batch_size=2,  # Smaller batch size for voice cloning (slower process)
    delay_between_requests=2.0,  # Longer delay for voice cloning API
    continue_on_error=True,
    tts_type="clone",  # Use "clone" instead of "synthesize"
)

# Summary is already printed by DatasetGenerator._log_summary()
# No need to print again
