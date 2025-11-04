import requests
import tempfile
import os
import json
from difflib import SequenceMatcher
import sys
from pathlib import Path
from typing import List, Dict, Union, Optional
from dataclasses import dataclass, asdict
import numpy as np
import unicodedata
import re
import string

def preprocess_text(text: str) -> str:
    """Normalize a single text string (NFKC, lowercase, remove punctuation/hyphens)."""
    text = text.strip()
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = text.replace("-", " ")
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    return text

def get_cer(ref, hyp):
    r = list(ref.replace(" ", ""))
    h = list(hyp.replace(" ", ""))
    d = np.zeros((len(r) + 1, len(h) + 1), dtype=np.uint16)
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j


    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1,
                          d[i][j - 1] + 1,
                          d[i - 1][j - 1] + cost)


    ref_html, hyp_html = [], []
    i, j = len(r), len(h)
    S, D, I = 0, 0, 0
    styles = {
        "substitute": "background-color: #fff3cd; padding: 2px 4px; border-radius: 3px;",
        "insert": "background-color: #d4edda; padding: 2px 4px; border-radius: 3px;",
        "delete": "background-color: #f8d7da; text-decoration: line-through; padding: 2px 4px; border-radius: 3px;"
    }


    while i > 0 or j > 0:
        cost = 0 if (i > 0 and j > 0 and r[i-1] == h[j-1]) else 1
        if i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + cost:
            if cost == 0:
                ref_html.insert(0, r[i-1])
                hyp_html.insert(0, h[j-1])
            else:
                S += 1
                ref_html.insert(0, f'<span style="{styles["substitute"]}">{r[i-1]}</span>')
                hyp_html.insert(0, f'<span style="{styles["substitute"]}">{h[j-1]}</span>')
            i -= 1
            j -= 1
        elif i > 0 and d[i][j] == d[i-1][j] + 1:
            D += 1
            ref_html.insert(0, f'<span style="{styles["delete"]}">{r[i-1]}</span>')
            hyp_html.insert(0, f'<span style="{styles["delete"]}">---</span>')
            i -= 1
        else:
            I += 1
            ref_html.insert(0, f'<span style="{styles["insert"]}">---</span>')
            hyp_html.insert(0, f'<span style="{styles["insert"]}">{h[j-1]}</span>')
            j -= 1


    N = max(1, len(r))
    cer = (S + D + I) / N
    return cer, S, D, I, N, "".join(ref_html), "".join(hyp_html)

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.gtts_provider import GTTSProvider
from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

@dataclass
class TTSSTTResult:
    """Class to store TTS-STT test results for a single text"""
    input_text: str
    stt_text: str
    cer: float
    substitutions: int
    deletions: int
    insertions: int
    is_exact_match: bool
    voice: str
    provider: str
    error: Optional[str] = None

def test_tts_stt(text: str, voice: str = "Hà My", provider: str = "vnpost") -> TTSSTTResult:
    """
    Test TTS-STT pipeline for a single text
    
    Args:
        text: Input text to test
        voice: Voice to use for TTS
        provider: TTS provider to use (vnpost, gtts, gemini)
        
    Returns:
        TTSSTTResult object containing test results
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
        normalized_input_text = preprocess_text(text)
        normalized_stt_text = preprocess_text(stt_text)

        cer, s, d, i, n, _, _ = get_cer(normalized_input_text, normalized_stt_text)
        is_exact = (normalized_input_text == normalized_stt_text)

        return TTSSTTResult(
            input_text=text,
            stt_text=stt_text,
            cer=round(cer, 3),
            substitutions=s,
            deletions=d,
            insertions=i,
            is_exact_match=is_exact,
            voice=voice,
            provider=provider
        )

    finally:
        # --- Dọn file ---
        if os.path.exists(tts_file_path):
            os.remove(tts_file_path)
def test_tts_stt_batch(texts: List[str], voice: str = "Hà My", provider: str = "vnpost") -> List[TTSSTTResult]:
    """
    Test TTS-STT pipeline for multiple texts
    
    Args:
        texts: List of input texts to test
        voice: Voice to use for TTS
        provider: TTS provider to use (vnpost, gtts, gemini)
        
    Returns:
        List of TTSSTTResult objects containing test results for each text
    """
    results = []
    for text in texts:
        try:
            result = test_tts_stt(text, voice, provider)
            results.append(result)
            print(f"✅ Tested: {text[:50]}... (CER: {result.cer:.2f})")
        except Exception as e:
            print(f"❌ Error processing text: {text[:50]}... - {str(e)}")
            results.append(TTSSTTResult(
                input_text=text,
                stt_text="",
                cer=1.0,
                substitutions=0,
                deletions=len(text),
                insertions=0,
                is_exact_match=False,
                voice=voice,
                provider=provider,
                error=str(e)
            ))
    return results

def print_results(results: Union[TTSSTTResult, List[TTSSTTResult]], output_file: Optional[str] = None):
    """Print test results in a readable format"""
    if not isinstance(results, list):
        results = [results]
        
    output = []
    total = len(results)
    exact_matches = sum(1 for r in results if r.is_exact_match)
    avg_cer = sum(r.cer for r in results) / total if total > 0 else 0
    
    # Summary
    summary = f"""
    ===== TTS-STT Test Results =====
    Total tests: {total}
    Exact matches: {exact_matches} ({exact_matches/total*100:.1f}%)
    Average CER: {avg_cer:.3f}
    ==============================
    """
    
    # Detailed results
    details = []
    for i, result in enumerate(results, 1):
        details.append(f"\n[{i}/{total}] Voice: {result.voice}, Provider: {result.provider}")
        details.append(f"Input: {result.input_text}")
        details.append(f"STT  : {result.stt_text}")
        details.append(f"CER: {result.cer:.3f} (S: {result.substitutions}, D: {result.deletions}, I: {result.insertions})")
        if result.error:
            details.append(f"❌ Error: {result.error}")
    
    # Combine and print
    full_output = summary + "\n".join(details)
    print(full_output)
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {output_file}")
    
    return full_output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test TTS-STT pipeline")
    parser.add_argument("--text", type=str, default="Xin chào, tôi là Hà My.",
                       help="Input text to test (or path to a text file with one text per line)")
    parser.add_argument("--voice", type=str, default="Hà My",
                       help="Voice to use for TTS")
    parser.add_argument("--provider", type=str, default="vnpost",
                       choices=["vnpost", "gtts", "gemini"],
                       help="TTS provider to use (default: vnpost)")
    parser.add_argument("--output", type=str, default="tts_stt_results.json",
                       help="Output file to save results (JSON format)")
    parser.add_argument("--batch", action="store_true",
                       help="Treat --text as a path to a text file with one text per line")
    
    args = parser.parse_args()
    
    try:
        if args.batch:
            # Read texts from file
            with open(args.text, 'r', encoding='utf-8') as f:
                texts = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(texts)} texts from {args.text}")
            results = test_tts_stt_batch(texts, args.voice, args.provider)
        else:
            # Single text
            results = [test_tts_stt(args.text, args.voice, args.provider)]
        
        # Print and save results
        print_results(results, args.output)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    print(results)



# Example Usage

# python /home/nampv1/projects/tts/speech-synth-engine/tests/test_tts_stt.py \
# --text "trà" \
# --voice "vi" \
# --provider "gtts"

# python /home/nampv1/projects/tts/speech-synth-engine/tests/test_tts_stt.py \
# --text "/home/nampv1/projects/asr/asr_ft/notebooks/error_analysis/VoA/confusable_words_list _top20.txt" \
# --voice "vi" \
# --provider "gtts" \
# --batch

