#!/usr/bin/env python3
# ============================================================
# Provider Factory System
# Factory pattern for creating and managing TTS providers
# ============================================================

import os
import sys
import importlib
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import logging
import yaml
from ...schemas.provider import ProviderConfig

# Add current directory to path để import được các providers
current_dir = Path(__file__).parent.parent.parent
# sys.path.insert(0, str(current_dir))

from .provider import TTSProvider, ProviderCapabilities

class ProviderFactory:
    """
    Factory for creating TTS Provider instances from configuration.
    Supports auto-discovery and dynamic loading of providers.
    """

    def __init__(self):
        self.logger = logging.getLogger("ProviderFactory")
        self._loaded_providers = {}
        self._provider_classes = {}

        # Register built-in providers
        self._register_builtin_providers()

    def _register_builtin_providers(self):
        """Register built-in providers"""
        try:
            from ..gtts_provider import GTTSProvider
            from ..gemini_provider import GeminiTTSProvider
            from ..vnpost_provider import VnPostTTSProvider
            from ..minimax_selenium_provider import MiniMaxSeleniumProvider
            from ..elevenlabs_provider import ElevenLabsProvider
            from ..cartesia_provider import CartesiaTTSProvider
            from ..xiaomi_provider import XiaomiTTSProvider

            self._provider_classes.update({
                'gtts': GTTSProvider,        
                'gemini': GeminiTTSProvider, 
                'vnpost': VnPostTTSProvider,
                'minimax_selenium': MiniMaxSeleniumProvider,
                'elevenlabs': ElevenLabsProvider,
                'cartesia': CartesiaTTSProvider,
                'xiaomi': XiaomiTTSProvider,
            })

            self.logger.debug(f"Registered {len(self._provider_classes)} built-in providers")

        except ImportError as e:
            self.logger.warning(f"⚠️ Cannot import some providers: {e}")
            self.logger.exception("Detailed error:")

    def register_provider_class(self, name: str, provider_class: Type[TTSProvider]):
        """Register additional provider class"""
        self._provider_classes[name.lower()] = provider_class
        self.logger.info(f"✅ Registered provider class: {name}")

    def create_provider(self, provider_name: str, config: Dict[str, Any] = None) -> TTSProvider:
        """
        Create provider instance from name and config.

        Args:
            provider_name: Provider name ('gtts', 'gemini', 'cartesia', etc.)
            config: Configuration for the provider

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider is not supported or config is invalid
        """
        config = config or {}

        # Validate optional provider_config:
        # - If it's already a ProviderConfig instance, keep as-is
        # - If it's a dict, validate and normalize
        # Keep a reference to ProviderConfig instance if one was provided
        pcfg_obj = config.get('provider_config') if isinstance(config, dict) else None
        try:
            if isinstance(pcfg_obj, ProviderConfig):
                # already validated
                pass
            elif isinstance(pcfg_obj, dict):
                validated = ProviderConfig.model_validate(pcfg_obj)
                # Keep dict form for serialization friendliness
                config['provider_config'] = validated.model_dump()
                pcfg_obj = validated  # store instance for potential fallback
        except Exception as e:
            self.logger.warning(f"provider_config validation failed for '{provider_name}': {e}")

        # Find provider class
        provider_class = self._provider_classes.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Provider '{provider_name}' is not supported. "
                           f"Available providers: {list(self._provider_classes.keys())}")

        try:
            # Prefer legacy signature (name, config=...)
            provider = provider_class(name=provider_name, config=config)
        except TypeError:
            # Fallback to (name, provider_config=...)
            try:
                provider = provider_class(name=provider_name, provider_config=pcfg_obj if isinstance(pcfg_obj, ProviderConfig) else None)
            except Exception as e:
                raise ValueError(f"Error creating provider {provider_name} with provider_config: {e}")
        except Exception as e:
            raise ValueError(f"Error creating provider {provider_name}: {e}")

        # Validate provider type
        if not isinstance(provider, TTSProvider):
            raise ValueError(f"Provider {provider_name} is not a TTSProvider")

        self.logger.debug(f"Created provider: {provider_name}")
        return provider

    def create_providers_from_config(self, config_file: Path) -> Dict[str, TTSProvider]:
        """
        Create multiple providers from YAML configuration file.

        Args:
            config_file: Path to YAML config file

        Returns:
            Dict containing provider instances by name
        """
        if not config_file.exists():
            raise FileNotFoundError(f"Config file does not exist: {config_file}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not isinstance(config_data, dict):
                raise ValueError("Config file must contain a dictionary")

            providers_config = config_data.get('providers', {})
            if not providers_config:
                raise ValueError("Config file must have 'providers' section")

            providers = {}

            for provider_name, provider_config in providers_config.items():
                try:
                    provider = self.create_provider(provider_name, provider_config)
                    providers[provider_name] = provider

                except Exception as e:
                    self.logger.error(f"❌ Error creating provider {provider_name}: {e}")
                    # Continue with other providers
                    continue

            self.logger.info(f"✅ Created {len(providers)} providers from config")
            return providers

        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML config: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file: {e}")

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a provider"""
        provider = self._loaded_providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} has not been created")

        return provider.get_metadata_info()

    def get_all_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all created providers"""
        return {name: provider.get_metadata_info()
                for name, provider in self._loaded_providers.items()}

    def get_capabilities(self, provider_name: str) -> ProviderCapabilities:
        """Get capabilities of a provider"""
        provider = self._loaded_providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} has not been created")

        return ProviderCapabilities(provider_name)

    def list_available_providers(self) -> List[str]:
        """List available providers"""
        return list(self._provider_classes.keys())

    def list_loaded_providers(self) -> List[str]:
        """List loaded providers"""
        return list(self._loaded_providers.keys())

    def cleanup_provider(self, provider_name: str):
        """Clean up provider and release resources"""
        if provider_name in self._loaded_providers:
            del self._loaded_providers[provider_name]
            self.logger.info(f"✅ Cleaned up provider: {provider_name}")

    def cleanup_all_providers(self):
        """Clean up all providers"""
        count = len(self._loaded_providers)
        self._loaded_providers.clear()
        self.logger.info(f"✅ Cleaned up {count} providers")


# Global factory instance
provider_factory = ProviderFactory()
