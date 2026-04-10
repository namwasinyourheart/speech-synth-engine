# https://docs.synthflow.ai/voice-configuration#advanced-settings
# Advanced Settings:
# - stability
# - style exaggeration

from typing import Optional, Dict, Any
from pydantic import BaseModel

class SynthesisResult(BaseModel):
    """
    Unified return schema for synthesize_with_metadata across all providers.
    """
    success: bool
    text: str
    output_file: Optional[str] = None
    provider: str
    model: Optional[str] = None
    effective_voice_config: Optional[Dict[str, Any]] = None
    effective_audio_config: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

# - similarity