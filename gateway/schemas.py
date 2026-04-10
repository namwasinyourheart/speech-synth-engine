"""
Gateway request/response schemas for TTS API.
"""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class VoiceConfig(BaseModel):
    """Voice configuration for TTS request."""
    voice_id: Optional[str] = Field(
        default=None,
        description="Voice identifier (e.g., 'pNInz6obpgDQGcFmaJgB' for ElevenLabs)"
    )
    reference_audio: Optional[str] = Field(
        default=None,
        description="Path to reference audio file for voice cloning (providers that support cloning)"
    )
    reference_text: Optional[str] = Field(
        default=None,
        description="Transcript of the reference audio (optional, improves cloning quality)"
    )
    enhance_speech: Optional[bool] = Field(
        default=None,
        description="Whether to enhance the reference audio before cloning"
    )
    volume: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Volume multiplier (0.0-1.0)"
    )
    speed: Optional[float] = Field(
        default=None,
        ge=0.5,
        le=2.0,
        description="Speech rate multiplier (0.5-2.0)"
    )
    emotion: Optional[str] = Field(
        default=None,
        description="Emotion or style tag (e.g., 'neutral', 'happy', 'sad')"
    )
    language: Optional[str] = Field(
        default=None,
        description="Language code (e.g., 'vi', 'en')"
    )
    pitch: Optional[float] = Field(
        default=None,
        description="Pitch adjustment in semitones"
    )


class AudioConfig(BaseModel):
    """Audio configuration for TTS request."""
    container: Optional[Literal["raw", "wav", "mp3"]] = Field(
        default=None,
        description="Audio container format"
    )
    encoding: Optional[Literal[
        "pcm_f32le", "pcm_s16le", "pcm_mulaw", "pcm_alaw", "mp3"
    ]] = Field(
        default=None,
        description="Audio encoding format"
    )
    sample_rate: Optional[Literal[8000, 16000, 22050, 24000, 32000, 44100]] = Field(
        default=None,
        description="Audio sample rate in Hz"
    )
    bit_rate: Optional[Literal["64kbps", "128kbps", "192kbps", "256kbps", "320kbps"]] = Field(
        default=None,
        description="Audio bit rate"
    )
    channel: Optional[Literal[1, 2]] = Field(
        default=None,
        description="Number of audio channels (1=mono, 2=stereo)"
    )


class TTSRequest(BaseModel):
    """
    TTS synthesis request schema.
    
    Example:
        {
            "provider": "cartesia",
            "model": "sonic-3",
            "text": "Xin chào, đây là giọng nói được tạo ra.",
            "voice_config": {
                "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
                "volume": 1.0,
                "speed": 1.0,
                "emotion": "neutral",
                "language": "vi"
            },
            "audio_config": {
                "container": "mp3",
                "encoding": "pcm_f32le",
                "sample_rate": 44100
            }
        }
    """
    provider: str = Field(
        description="TTS provider name (e.g., 'cartesia', 'gemini', 'gtts', 'elevenlabs', 'xiaomi', 'vnpost')"
    )
    text: str = Field(
        description="Text to synthesize into speech",
        min_length=1
    )
    model: Optional[str] = Field(
        default=None,
        description="Model identifier (provider-specific)"
    )
    voice_config: Optional[VoiceConfig] = Field(
        default=None,
        description="Voice configuration including voice_id, volume, speed, emotion, language"
    )
    audio_config: Optional[AudioConfig] = Field(
        default=None,
        description="Audio configuration including container, encoding, sample_rate"
    )


class TTSError(BaseModel):
    """Error details for failed synthesis."""
    message: str
    detail: Optional[str] = None


class TTSResponse(BaseModel):
    """
    TTS synthesis response schema.
    
    Example success:
        {
            "success": true,
            "text": "Xin chào, đây là giọng nói được tạo ra.",
            "audio_url": "/audio/output_12345.mp3",
            "provider": "cartesia",
            "model": "sonic-3",
            "effective_voice_config": {...},
            "effective_audio_config": {...}
        }
    
    Example failure:
        {
            "success": false,
            "text": "Xin chào...",
            "audio_url": null,
            "provider": "cartesia",
            "error": {
                "message": "Synthesis failed",
                "detail": "API rate limit exceeded"
            }
        }
    """
    success: bool
    text: str
    audio_url: Optional[str] = None
    provider: str
    model: Optional[str] = None
    effective_voice_config: Optional[Dict[str, Any]] = None
    effective_audio_config: Optional[Dict[str, Any]] = None
    error: Optional[TTSError] = None


class ProviderInfo(BaseModel):
    """Provider information for listing available providers."""
    name: str
    supported_voices: list
    supported_models: Optional[list] = None
    sample_rate: Optional[int] = None
    language: Optional[str] = None
    config: Dict[str, Any]


class HealthStatus(BaseModel):
    """Health check status for a provider."""
    provider: str
    status: Literal["healthy", "unhealthy", "unknown"]
    message: Optional[str] = None


class CloneRequest(BaseModel):
    """
    Voice cloning request schema (used with multipart/form upload).
    
    Fields typically sent as form data:
    - provider: str (required)
    - text: str (required)
    - model: Optional[str]
    - reference_text: Optional[str] - transcript of reference audio
    - language: Optional[str]
    - enhance_speech: Optional[bool]
    - volume/speed/pitch/emotion: Optional
    
    Files:
    - reference_audio: UploadFile (required) - audio file to clone voice from
    """
    provider: str = Field(description="TTS provider name (e.g., 'xiaomi', 'minimax_selenium')")
    text: str = Field(description="Text to synthesize using cloned voice")
    model: Optional[str] = Field(default=None, description="Model identifier (provider-specific)")
    reference_text: Optional[str] = Field(default=None, description="Transcript of reference audio (optional)")
    language: Optional[str] = Field(default=None, description="Language code (e.g., 'vi', 'en')")
    enhance_speech: Optional[bool] = Field(default=None, description="Enhance reference audio before cloning")
    volume: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    speed: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(default=None)
    emotion: Optional[str] = Field(default=None)


__all__ = [
    "VoiceConfig",
    "AudioConfig",
    "TTSRequest",
    "TTSError",
    "TTSResponse",
    "ProviderInfo",
    "HealthStatus",
    "CloneRequest",
]
