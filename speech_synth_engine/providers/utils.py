"""
Utility functions for TTS providers.
Shared helpers for API key resolution, config extraction, etc.
"""

import os
from typing import Any, Dict, List, Optional, TypeVar, Union


def resolve_api_key(
    config: Dict[str, Any],
    provider_config: Optional[Any] = None,
    fallback_env_var: str = None,
) -> Optional[str]:
    """
    Resolve API key ONLY from ProviderConfig and environment.

    Priority:
    1. provider_config.credentials.api_keys (string or list)
    2. Environment variables listed in provider_config.credentials.envs
    3. Fallback environment variable (e.g., 'CARTESIA_API_KEY')

    NOTE: Direct config['api_keys'] is intentionally ignored to enforce
    a single source of truth via ProviderConfig.

    Args:
        config: Provider runtime config (ignored for api_keys)
        provider_config: Optional ProviderConfig with credentials
        fallback_env_var: Fallback env var name

    Returns:
        API key string if found, else None
    """
    api_key: Optional[str] = None

    # 1) From ProviderConfig.credentials.api_keys
    if provider_config:
        try:
            cred_api_keys = getattr(provider_config.credentials, 'api_keys', None)
            if isinstance(cred_api_keys, str) and cred_api_keys.strip():
                api_key = cred_api_keys.strip()
            elif isinstance(cred_api_keys, list) and cred_api_keys:
                for k in cred_api_keys:
                    if str(k).strip():
                        api_key = str(k).strip()
                        break
        except (AttributeError, TypeError):
            pass

    # 2) From envs listed in ProviderConfig.credentials.envs
    if not api_key and provider_config:
        try:
            env_names = getattr(provider_config.credentials, 'envs', []) or []
            for env_name in env_names:
                val = os.getenv(env_name)
                if val and str(val).strip():
                    api_key = str(val).strip()
                    break
        except (AttributeError, TypeError):
            pass

    # 3) Fallback env var
    if not api_key and fallback_env_var:
        env_key = os.getenv(fallback_env_var)
        if env_key and env_key.strip():
            api_key = env_key.strip()

    return api_key


T = TypeVar('T')


def get_config_value(
    config_obj: Optional[Any],
    attr_name: str,
    default: T,
) -> Union[T, Any]:
    """
    Safely get attribute from config object with fallback to default.
    
    Args:
        config_obj: Config object (e.g., VoiceConfig, AudioConfig)
        attr_name: Attribute name to retrieve
        default: Default value if attribute not found or is None
        
    Returns:
        Attribute value or default
        
    Examples:
        >>> voice_cfg = VoiceConfig(voice_id="abc", volume=0.8)
        >>> get_config_value(voice_cfg, 'volume', 1.0)
        0.8
        >>> get_config_value(voice_cfg, 'speed', 1.0)
        1.0
        >>> get_config_value(None, 'speed', 1.0)
        1.0
    """
    if config_obj is None:
        return default
    
    value = getattr(config_obj, attr_name, None)
    return value if value is not None else default


def extract_voice_params(
    voice_config: Optional[Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract voice parameters from VoiceConfig with defaults.
    
    Args:
        voice_config: VoiceConfig object or None
        defaults: Dictionary of default values
        
    Returns:
        Dictionary with resolved voice parameters
        
    Example:
        >>> defaults = {'volume': 1.0, 'speed': 1.0, 'emotion': 'neutral', 'language': 'vi'}
        >>> params = extract_voice_params(voice_config, defaults)
        >>> # params = {'voice_id': '...', 'volume': 0.8, 'speed': 1.2, ...}
    """
    params = {}
    
    for key, default_value in defaults.items():
        params[key] = get_config_value(voice_config, key, default_value)
    
    return params


def extract_audio_params(
    audio_config: Optional[Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract audio parameters from AudioConfig with defaults.
    
    Args:
        audio_config: AudioConfig object or None
        defaults: Dictionary of default values
        
    Returns:
        Dictionary with resolved audio parameters
        
    Example:
        >>> defaults = {'container': 'mp3', 'encoding': 'pcm_f32le', 'sample_rate': 44100}
        >>> params = extract_audio_params(audio_config, defaults)
    """
    params = {}
    
    for key, default_value in defaults.items():
        params[key] = get_config_value(audio_config, key, default_value)
    
    return params


def validate_enum_value(
    value: Any,
    allowed_values: List[Any],
    param_name: str,
    logger: Optional[Any] = None,
) -> bool:
    """
    Validate that a value is in the allowed list.
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        param_name: Parameter name for logging
        logger: Optional logger for warnings
        
    Returns:
        True if valid, False otherwise (with warning logged)
    """
    if value not in allowed_values:
        if logger:
            logger.warning(
                f"{param_name} '{value}' may not be supported. "
                f"Recommended values: {allowed_values}"
            )
        return False
    return True
