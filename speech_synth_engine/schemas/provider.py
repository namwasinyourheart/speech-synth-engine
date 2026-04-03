from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CredentialsConfig(BaseModel):
    """
    Holds environment variable configuration for a provider's authentication.

    - envs: List of acceptable environment variable names (e.g., GEMINI_API_KEY, GCP_CREDENTIAL_PATH).
    - required: Subset of envs that must be present for a specific mode (e.g., Vertex AI).
    - notes: Optional human-readable guidance.
    """
    envs: List[str] = Field(default_factory=list)
    required: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


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


__all__ = ["CredentialsConfig", "ProviderConfig"]