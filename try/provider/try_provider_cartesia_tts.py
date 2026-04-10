import sys
import os

# sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from rich import print

from datetime import datetime
from pathlib import Path
from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig, VoiceConfig, AudioConfig
from speech_synth_engine.providers.cartesia_provider import CartesiaTTSProvider

# Build configs
credentials_cfg = CredentialsConfig(
    envs=["CARTESIA_API_KEY"],
    api_keys=["sk_car_kyo1L9tkE8H6khB2eL1fTV"],
)

pcfg = ProviderConfig(
    name="cartesia",
    models=["sonic-3"],
    default_model="sonic-3",
    credentials=credentials_cfg,
)

# Optional per-request configs
voice_cfg = VoiceConfig(
    # voice_id="b8cd71e3-bc14-4538-a530-d6314731c036",  # female_south
    voice_id="0e58d60a-2f1a-4252-81bd-3db6af45fb41",  # male_central
    volume=1.0,
    speed=1.0,
    emotion="neutral",
    language="vi",
)
audio_cfg = AudioConfig(
    container="mp3",
    encoding="pcm_f32le",
    sample_rate=44100,
)

provider = CartesiaTTSProvider(
    name="cartesia",
    provider_config=pcfg,
)

text=(
        "World Cup 2026 sẽ diễn ra từ ngày 11/6 đến 19/7 tại Mỹ, Mexico và Canada, "
        "với tổng cộng 16 thành phố đăng cai. Trận khai mạc giữa Mexico và Nam Phi "
        "diễn ra vào lúc 2h ngày 12/6 (theo giờ Việt Nam)."
    )
text = "Nhiều thông điệp quan trọng về vai trò của Quốc hội trong khóa mới được Tổng Bí thư Tô Lâm gợi mở và định hướng trong bài phát biểu quan trọng tại phiên khai mạc kỳ họp thứ nhất Quốc hội khóa XVI. \nKỳ họp này, theo Tổng Bí thư, có ý nghĩa đặc biệt quan trọng, mở đầu cho một nhiệm kỳ mới của cơ quan đại biểu cao nhất của Nhân dân, cơ quan quyền lực Nhà nước cao nhất của nước ta."

from speech_synth_engine.schemas.generation import GenerateSpeechConfig

gen_cfg = GenerateSpeechConfig(
    model="sonic-3",
    voice_config=voice_cfg,
    audio_config=audio_cfg,
)

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
text_in_filename = "_".join(text[:50].split())
ok = provider.synthesize_with_metadata(
    text=text,
    output_file=Path(
        f"/home/nampv1/projects/tts/speech-synth-engine/try/output/try-cartesia-tts/wavs/try_cartesia_{text_in_filename}_{current_time}.mp3"
    ),
    generation_config=gen_cfg,
)
print("Success:", ok)
