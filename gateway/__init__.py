"""
TTS Gateway - Unified API for Text-to-Speech synthesis.

This package provides a gateway for routing TTS requests to multiple providers.
"""

from .schemas import TTSRequest, TTSResponse, VoiceConfig, AudioConfig
from .router import ProviderRouter, DirectProviderAdapter
from .config import GatewayConfig, ProviderEnvConfig

__version__ = "1.0.0"
__all__ = [
    "TTSRequest",
    "TTSResponse",
    "VoiceConfig",
    "AudioConfig",
    "ProviderRouter",
    "DirectProviderAdapter",
    "GatewayConfig",
    "ProviderEnvConfig",
]
