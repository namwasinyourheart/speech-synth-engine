import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

import pytest
from pathlib import Path
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

@pytest.fixture
def gemini_provider():
    # Khởi tạo GeminiTTSProvider fixture
    return GeminiTTSProvider()

def test_synthesize_creates_file(tmp_path, gemini_provider):
    """
    Kiểm tra GeminiTTSProvider.synthesize có tạo file WAV đúng.
    """
    text = "Xin chào, hôm nay bạn khỏe không?"
    output_file = tmp_path / "test_output.wav"

    # Gọi synthesize
    gemini_provider.synthesize(text, voice="default", output_file=output_file)

    # Kiểm tra file tồn tại
    assert output_file.exists(), "WAV file không được tạo ra"

    # Kiểm tra file không rỗng
    assert output_file.stat().st_size > 0, "File WAV rỗng"
