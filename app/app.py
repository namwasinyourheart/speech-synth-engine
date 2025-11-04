import gradio as gr
import os
import tempfile
import requests
import subprocess
import numpy as np
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import TTS providers
from speech_synth_engine.providers.gtts_provider import GTTSProvider
from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

# STT endpoint
STT_URL = "https://ai.vnpost.vn/voiceai/core/stt/v1/file"

def get_tts_provider(provider_name, voice):
    """Initialize and return the appropriate TTS provider."""
    if provider_name == "vnpost":
        config = {
            'api_url': 'https://ai.vnpost.vn/voiceai/core/tts/v1/synthesize',
            'sample_rate': 22050,
            'voice': voice,
            'language': 'vi'
        }
        return VnPostTTSProvider("vnpost", config), voice
    
    elif provider_name == "gtts":
        config = {
            "sample_rate": 22050,
            "language": "vi",
            "chars_per_second": 12
        }
        return GTTSProvider("gtts", config), "vi"
    
    elif provider_name == "gemini":
        config = {
            'api_key': os.getenv('GEMINI_API_KEY', ''),
            'model': 'gemini-2.5-flash-preview-tts',
            'voice': voice,
            'language': 'vi',
        }
        return GeminiTTSProvider("gemini", config), voice
    
    raise ValueError(f"Unsupported provider: {provider_name}")

def process_tts_stt(text, provider, voice):
    """Process TTS and STT pipeline."""
    try:
        # Initialize TTS provider
        tts_provider, use_voice = get_tts_provider(provider, voice)
        
        # Create temp file for audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            tts_file_path = tmp_audio.name
        
        # Generate TTS
        success = tts_provider.synthesize(text, use_voice, Path(tts_file_path))
        if not success:
            return None, None, None, f"❌ TTS generation failed using {provider}"
        
        # Call STT
        with open(tts_file_path, "rb") as audio_file:
            stt_response = requests.post(
                STT_URL,
                files={
                    "audio_file": audio_file,
                    "enhance_speech": (None, "true"),
                    "postprocess_text": (None, "true"),
                },
            )
        
        # Clean up temp file
        os.unlink(tts_file_path)
        
        if stt_response.status_code != 200:
            return None, None, None, f"❌ STT error: {stt_response.status_code}, {stt_response.text}"
        
        stt_text = stt_response.json().get("text", "").strip()
        
        # Calculate similarity
        similarity = calculate_similarity(text, stt_text)
        is_match = similarity > 0.9  # 90% similarity threshold
        
        return tts_file_path, stt_text, f"{similarity:.2%}", None
        
    except Exception as e:
        return None, None, None, f"❌ Error: {str(e)}"

def calculate_similarity(original, generated):
    """Calculate similarity ratio between original and generated text."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, original.lower(), generated.lower()).ratio()

def create_tts_stt_tab():
    """Create the TTS/STT tab."""
    with gr.Blocks() as tab:
        gr.Markdown("# 🎙️ TTS/STT Pipeline")
        gr.Markdown("Convert text to speech and back to text to test the pipeline.")
        
        with gr.Row():
            with gr.Column(scale=2):
                input_text = gr.Textbox(
                    label="Input Text",
                    placeholder="Enter text to convert to speech...",
                    lines=5,
                    value="Xin chào, tôi là trợ lý ảo."
                )
                
                with gr.Row():
                    provider = gr.Dropdown(
                        label="TTS Provider",
                        choices=["vnpost", "gtts", "gemini"],
                        value="vnpost"
                    )
                    voice = gr.Dropdown(
                        label="Voice",
                        choices=["Hà My", "Minh Quang"],
                        value="Hà My"
                    )
                
                submit_btn = gr.Button("Generate Speech & Transcribe", variant="primary")
                
            with gr.Column(scale=1):
                audio_output = gr.Audio(label="Generated Speech", type="filepath")
                stt_output = gr.Textbox(label="Recognized Text")
                similarity_score = gr.Textbox(label="Similarity Score")
        
        error_output = gr.Textbox(label="Status", interactive=False, visible=False)
        
        # Update voice options based on provider
        def update_voice_options(provider):
            if provider == "vnpost":
                return gr.Dropdown(choices=["Hà My", "Minh Quang"], value="Hà My")
            elif provider == "gtts":
                return gr.Dropdown(choices=["vi"], value="vi")
            elif provider == "gemini":
                return gr.Dropdown(choices=["Kore", "Jade", "Nova", "Coral", "Ash"], value="Kore")
            return gr.Dropdown(choices=[], value="")
        
        provider.change(
            update_voice_options,
            inputs=[provider],
            outputs=[voice]
        )
        
        # Handle form submission
        def on_submit(text, provider, voice):
            audio_path, stt_text, similarity, error = process_tts_stt(text, provider, voice)
            if error:
                return {
                    audio_output: None,
                    stt_output: "",
                    similarity_score: "",
                    error_output: gr.Textbox(value=error, visible=True)
                }
            return {
                audio_output: audio_path,
                stt_output: stt_text,
                similarity_score: f"Similarity: {similarity}",
                error_output: gr.Textbox(value="✅ Processing completed successfully!", visible=False)
            }
        
        submit_btn.click(
            fn=on_submit,
            inputs=[input_text, provider, voice],
            outputs=[audio_output, stt_output, similarity_score, error_output]
        )
    
    return tab

def vietnamese_g2p(text):
    """Chuyển văn bản tiếng Việt → chuỗi phoneme IPA bằng eSpeak-ng"""
    try:
        result = subprocess.run(
            ["espeak-ng", "-v", "vi", "--ipa", "-q", text],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error in phoneme conversion: {str(e)}"

def phoneme_error_rate(ref_phonemes, hyp_phonemes):
    """Tính PER bằng Levenshtein distance"""
    ref = ref_phonemes.split()
    hyp = hyp_phonemes.split()
    n, m = len(ref), len(hyp)
    
    if n == 0:
        return 0.0 if m == 0 else 1.0
    
    dp = np.zeros((n+1, m+1), dtype=int)

    for i in range(1, n+1): 
        dp[i][0] = i
    for j in range(1, m+1): 
        dp[0][j] = j

    for i in range(1, n+1):
        for j in range(1, m+1):
            if ref[i-1] == hyp[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    return dp[n][m] / n

def create_phoneme_tab():
    """Create the Phoneme Analysis tab."""
    with gr.Blocks() as tab:
        gr.Markdown("# 🔤 Phoneme Analysis")
        gr.Markdown("Convert Vietnamese text to phonemes and calculate Phoneme Error Rate (PER).")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Input Text")
                reference_text = gr.Textbox(
                    label="Reference Text",
                    placeholder="Enter reference text...",
                    lines=3,
                    value="Xin chào, tôi là trợ lý ảo."
                )
                hypothesis_text = gr.Textbox(
                    label="Hypothesis Text",
                    placeholder="Enter hypothesis text to compare...",
                    lines=3,
                    value="Xin chào, tôi là trợ lý ảo."
                )
                analyze_btn = gr.Button("Analyze Phonemes", variant="primary")
                
            with gr.Column():
                gr.Markdown("### Phoneme Analysis Results")
                with gr.Row():
                    ref_phonemes = gr.Textbox(
                        label="Reference Phonemes",
                        interactive=False,
                        lines=3
                    )
                    hyp_phonemes = gr.Textbox(
                        label="Hypothesis Phonemes",
                        interactive=False,
                        lines=3
                    )
                per_score = gr.Textbox(
                    label="Phoneme Error Rate (PER)",
                    interactive=False
                )
        
        def analyze_phonemes(ref_text, hyp_text):
            """Analyze phonemes and calculate PER."""
            try:
                # Convert text to phonemes
                ref_ph = vietnamese_g2p(ref_text)
                hyp_ph = vietnamese_g2p(hyp_text)
                
                # Calculate PER
                per = phoneme_error_rate(ref_ph, hyp_ph)
                
                return {
                    ref_phonemes: ref_ph,
                    hyp_phonemes: hyp_ph,
                    per_score: f"{per:.2%}"
                }
            except Exception as e:
                return {
                    ref_phonemes: "Error",
                    hyp_phonemes: "Error",
                    per_score: f"Error: {str(e)}"
                }
        
        analyze_btn.click(
            fn=analyze_phonemes,
            inputs=[reference_text, hypothesis_text],
            outputs=[ref_phonemes, hyp_phonemes, per_score]
        )
    
    return tab

def main():
    """Create and launch the Gradio interface."""
    with gr.Blocks(theme=gr.themes.Soft(), title="Speech Synthesis Toolkit") as demo:
        gr.Markdown("# 🎙️ Speech Synthesis Toolkit")
        
        with gr.Tabs():
            with gr.TabItem("TTS/STT Pipeline"):
                tts_stt_tab = create_tts_stt_tab()
            
            with gr.TabItem("Phoneme Analysis"):
                phoneme_tab = create_phoneme_tab()
    
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)

if __name__ == "__main__":
    main()
