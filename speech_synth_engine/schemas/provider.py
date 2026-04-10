from __future__ import annotations

from typing import List, Optional, Union
from typing import Literal

from pydantic import BaseModel, Field


class CredentialsConfig(BaseModel):
    """
    Holds environment variable configuration for a provider's authentication.

    - envs: List of acceptable environment variable names (e.g., GEMINI_API_KEY, GCP_CREDENTIALS, GCP_PROJECT_ID, GCP_LOCATION).
    """
    envs: List[str] = Field(default_factory=list)
    # Optional API keys provided via schema (single string or list of strings)
    api_keys: Optional[Union[str, List[str]]] = None


class PrebuiltVoiceConfig(BaseModel):
    """Prebuilt voice configuration for providers using predefined voice IDs."""

    voice_id: Optional[str] = None
    language: Optional[str] = None
    volume: Optional[float] = Field(
        default=None,
        description="Volume multiplier (e.g., 0.0-1.0)"
    )
    speed: Optional[float] = Field(
        default=None,
        description="Speech rate multiplier (e.g., 0.5-2.0)"
    )
    pitch: Optional[float] = Field(
        default=None,
        description="Pitch adjustment in semitones"
    )
    emotion: Optional[str] = Field(
        default=None,
        description="Emotion or style tag supported by the provider"
    )


class ReplicatedVoiceConfig(BaseModel):
    """Replicated voice configuration for voice cloning from reference audio."""

    reference_audio: str = Field(
        description="Path to reference audio file for voice cloning"
    )
    reference_text: Optional[str] = Field(
        default=None,
        description="Transcript of the reference audio (optional, improves quality)"
    )
    enhance_speech: Optional[bool] = Field(
        default=False,
        description="Whether to apply speech enhancement to the reference audio"
    )
    language: Optional[str] = None
    volume: Optional[float] = Field(
        default=None,
        description="Volume multiplier (e.g., 0.0-1.0)"
    )
    speed: Optional[float] = Field(
        default=None,
        description="Speech rate multiplier (e.g., 0.5-2.0)"
    )
    pitch: Optional[float] = Field(
        default=None,
        description="Pitch adjustment in semitones"
    )
    emotion: Optional[str] = Field(
        default=None,
        description="Emotion or style tag supported by the provider"
    )


# Backward compatibility alias
VoiceConfig = PrebuiltVoiceConfig


class AudioConfig(BaseModel):
    """Audio configuration options for providers."""

    encoding: Optional[Literal[
        "pcm_f32le",
        "pcm_s16le",
        "pcm_mulaw",
        "pcm_alaw",
        "mp3",
    ]] = None
    container: Optional[Literal["raw", "wav", "mp3"]] = None
    bit_rate: Optional[Literal["64kbps", "128kbps", "192kbps", "256kbps", "320kbps"]] = None
    sample_rate: Optional[Literal[8000, 16000, 22050, 24000, 32000, 44100]] = None
    channel: Optional[Literal[1, 2]] = None


class ProviderConfig(BaseModel):
    """
    Provider configuration schema.

    - name: Provider name/key (e.g., "gemini").
    - models: List of available model identifiers.
    - default_model: Default model identifier (must be included in models).
    - credentials: CredentialsConfig describing envs and required subset.
    """

    name: str
    models: List[str]
    default_model: str
    credentials: CredentialsConfig


__all__ = [
    "CredentialsConfig",
    "ProviderConfig",
    "PrebuiltVoiceConfig",
    "ReplicatedVoiceConfig",
    "VoiceConfig",
    "AudioConfig",
]