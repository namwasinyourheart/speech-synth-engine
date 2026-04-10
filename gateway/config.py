"""
Gateway Configuration Manager

Loads and manages environment variables and configuration settings
for the TTS Gateway and its providers.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)


@dataclass
class ProviderEnvConfig:
    """Environment configuration for a single provider."""
    api_keys: List[str] = field(default_factory=list)
    api_key: Optional[str] = None  # For single-key providers
    base_url: Optional[str] = None
    model: Optional[str] = None
    region: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    # Xiaomi specific
    stt_api_base: Optional[str] = None
    stt_endpoint: Optional[str] = None
    clone_api_base: Optional[str] = None
    clone_endpoint: Optional[str] = None


class GatewayConfig:
    """
    Centralized configuration manager for TTS Gateway.
    
    Loads configuration from environment variables with sensible defaults.
    """
    
    # Gateway settings
    HOST: str = os.getenv("TTS_GATEWAY_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("TTS_GATEWAY_PORT", "8000"))
    RELOAD: bool = os.getenv("TTS_GATEWAY_RELOAD", "false").lower() == "true"
    
    # Output settings
    OUTPUT_DIR: Path = Path(os.getenv("TTS_OUTPUT_DIR", "./gateway_output"))
    UPLOAD_DIR: Path = Path(os.getenv("TTS_UPLOAD_DIR", "./gateway_output/uploads"))
    
    # Provider config file
    PROVIDERS_CONFIG_FILE: Path = Path(os.getenv("TTS_PROVIDERS_CONFIG", "./config/providers.yaml"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("TTS_LOG_LEVEL", "INFO")
    
    # CORS settings - use classmethod to return list
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get CORS allowed origins from environment."""
        origins = os.getenv(
            "TTS_CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"
        )
        return [o.strip() for o in origins.split(",") if o.strip()]

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """CORS allowed origins (for instance access)."""
        return self.get_cors_origins()
    
    @classmethod
    def get_provider_config(cls, provider_name: str) -> ProviderEnvConfig:
        """
        Get environment configuration for a specific provider.
        
        Args:
            provider_name: Name of the provider (e.g., 'cartesia', 'xiaomi')
            
        Returns:
            ProviderEnvConfig with loaded environment variables
        """
        name = provider_name.upper().replace("-", "_").replace(" ", "_")
        
        config = ProviderEnvConfig()
        
        # API Keys (comma-separated for multiple keys)
        api_keys_str = os.getenv(f"{name}_API_KEYS", "")
        if api_keys_str:
            config.api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        
        # Single API key
        config.api_key = os.getenv(f"{name}_API_KEY")
        
        # Base URL / Endpoint
        config.base_url = os.getenv(f"{name}_BASE_URL")
        config.model = os.getenv(f"{name}_MODEL")
        config.region = os.getenv(f"{name}_REGION")
        
        # Gemini Vertex AI
        if name == "GEMINI":
            config.vertex_project = os.getenv("GEMINI_VERTEX_PROJECT")
            config.vertex_location = os.getenv("GEMINI_VERTEX_LOCATION")
        
        # Xiaomi specific
        if name == "XIAOMI":
            config.stt_api_base = os.getenv("XIAOMI_STT_API_BASE")
            config.stt_endpoint = os.getenv("XIAOMI_STT_ENDPOINT")
            config.clone_api_base = os.getenv("XIAOMI_CLONE_API_BASE")
            config.clone_endpoint = os.getenv("XIAOMI_CLONE_ENDPOINT")
        
        # MiniMax specific
        if name == "MINIMAX" or name == "MINIMAX_SELENIUM":
            config.api_key = os.getenv("MINIMAX_API_KEY") or os.getenv("MINIMAX_SELENIUM_API_KEY")
        
        return config
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary for debugging."""
        return {
            "gateway": {
                "host": cls.HOST,
                "port": cls.PORT,
                "reload": cls.RELOAD,
                "log_level": cls.LOG_LEVEL,
            },
            "directories": {
                "output": str(cls.OUTPUT_DIR),
                "upload": str(cls.UPLOAD_DIR),
            },
            "providers_config": str(cls.PROVIDERS_CONFIG_FILE),
            "cors_origins": cls.CORS_ORIGINS,
        }


# Global config instance
config = GatewayConfig

__all__ = [
    "GatewayConfig",
    "ProviderEnvConfig",
    "config",
]
