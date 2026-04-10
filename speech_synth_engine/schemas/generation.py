from dataclasses import dataclass
from typing import Optional
from .provider import PrebuiltVoiceConfig, AudioConfig, ReplicatedVoiceConfig

@dataclass
class GenerateSpeechConfig:
    """
    Unified configuration for a speech generation job.
    Supports both prebuilt voices (via PrebuiltVoiceConfig) and voice cloning (via ReplicatedVoiceConfig).
    """
    model: str
    voice_config: PrebuiltVoiceConfig
    audio_config: Optional[AudioConfig] = None

@dataclass
class VoiceCloningConfig:
    """
    Unified configuration for a voice cloning job.
    """
    model: str
    voice_config: ReplicatedVoiceConfig
    audio_config: Optional[AudioConfig] = None

