import requests
import tempfile
import os
from difflib import SequenceMatcher
import sys
from pathlib import Path

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.gtts_provider import GTTSProvider
from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

def test_tts_stt(text, voice="Hà My", provider="vnpost"):
    """
    Kiểm thử vòng khép kín text -> TTS -> STT -> text
    Trả về:
        {
            "input_text": ...,
            "stt_text": ...,
            "similarity": 0.xx,
            "is_exact_match": True/False
        }
    """
    # STT endpoint (keeping external STT for now)
    STT_URL = "https://ai.vnpost.vn/voiceai/core/stt/v1/file"

    # Initialize TTS Provider based on selection
    if provider == "vnpost":
        tts_provider_config = {
            'api_url': 'https://ai.vnpost.vn/voiceai/core/tts/v1/synthesize',
            'sample_rate': 22050,
            'voice': voice,
            'language': 'vi'
        }
        tts_provider = VnPostTTSProvider("vnpost", tts_provider_config)
        use_voice = voice  # VNPost supports specific voice names

    elif provider == "gtts":
        gtts_provider_config = {
            "sample_rate": 22050,
            "language": "vi",
            "chars_per_second": 12
        }
        tts_provider = GTTSProvider("gtts", gtts_provider_config)
        # GTTS only supports language codes, not specific voice names
        use_voice = "vi"  # GTTS uses language codes instead of specific voice names

    elif provider == "gemini":
        # Import gemini provider config from config file
        gemini_provider_config = {
            'api_key': os.getenv('GEMINI_API_KEY', ''),
            # 'sample_rate': 22050,
            'model': 'gemini-2.5-flash-preview-tts',
            'voice': 'Kore',
            'language': 'vi',
            # 'chars_per_second': 15,
            # 'min_duration': 0.3,
            # 'max_duration': 8.0
        }
        tts_provider = GeminiTTSProvider("gemini", gemini_provider_config)
        if voice not in tts_provider.supported_voices:
            raise ValueError(f"Voice '{voice}' is not supported. Available voices: {tts_provider.supported_voices}")
        use_voice = voice

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # tạo file tạm để lưu audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        tts_file_path = tmp_audio.name

    try:
        # --- Bước 1: gọi TTS sử dụng local provider ---
        print(f"🎵 Generating TTS using provider {provider.upper()} for: {text[:50]}...")

        success = tts_provider.synthesize(text, use_voice, Path(tts_file_path))

        if not success:
            raise Exception(f"TTS generation failed using provider {provider.upper()}")

        print(f"✅ TTS generation successful: {tts_file_path}")

        # --- Bước 2: gọi STT ---
        stt_response = requests.post(
            STT_URL,
            files={
                "audio_file": open(tts_file_path, "rb"),
                "enhance_speech": (None, "true"),
                "postprocess_text": (None, "true"),
            },
        )

        if stt_response.status_code != 200:
            raise Exception(f"STT error: {stt_response.status_code}, {stt_response.text}")

        stt_json = stt_response.json()
        stt_text = stt_json.get("text", "").strip()

        # --- Bước 3: So sánh ---
        similarity = SequenceMatcher(None, text.lower(), stt_text.lower()).ratio()
        is_exact = text.strip().lower() == stt_text.strip().lower()

        return {
            "input_text": text,
            "stt_text": stt_text,
            "similarity": round(similarity, 3),
            "is_exact_match": is_exact,
        }

    finally:
        # --- Dọn file ---
        if os.path.exists(tts_file_path):
            os.remove(tts_file_path)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, default="Xin chào, tôi là Hà My.")
    parser.add_argument("--voice", type=str, default="Hà My")
    parser.add_argument("--provider", type=str, default="vnpost",
                       choices=["vnpost", "gtts", "gemini"],
                       help="TTS provider to use (default: vnpost)")
    args = parser.parse_args()

    result = test_tts_stt(
        text = args.text,
        voice = args.voice,
        provider = args.provider
    )
    result_str = (
        f"input_text: {result['input_text']}\n"
        f"stt_text: {result['stt_text']}\n"
        f"similarity: {result['similarity']}\n"
        f"is_exact_match: {result['is_exact_match']}"
    )
    print(result_str)