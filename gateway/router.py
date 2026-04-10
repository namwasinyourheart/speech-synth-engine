"""
Provider routing logic for TTS Gateway.

This module provides the abstraction layer between Gateway and Providers,
allowing easy migration from direct calls to HTTP API calls in the future.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from speech_synth_engine.providers.base.provider_factory import ProviderFactory
from speech_synth_engine.providers.base.provider import TTSProvider
from speech_synth_engine.schemas.schemas import SynthesisResult
from speech_synth_engine.schemas.provider import VoiceConfig, AudioConfig, ReplicatedVoiceConfig
from speech_synth_engine.schemas.generation import GenerateSpeechConfig, VoiceCloningConfig

from .schemas import TTSRequest, TTSResponse, TTSError, HealthStatus

logger = logging.getLogger("TTSGateway.Router")


class ProviderAdapter(ABC):
    """
    Abstract adapter interface for TTS providers.
    
    This abstraction allows the Gateway to work with providers
    regardless of whether they're called directly or via HTTP API.
    """
    
    @abstractmethod
    async def synthesize(self, request: TTSRequest, output_dir: Path) -> TTSResponse:
        """Execute TTS synthesis and return response."""
        pass
    
    @abstractmethod
    async def clone(self, request: TTSRequest, output_dir: Path) -> TTSResponse:
        """Execute voice cloning and return response."""
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check provider health status."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        pass


class DirectProviderAdapter(ProviderAdapter):
    """
    Adapter for direct in-process provider calls.
    
    Currently used for all providers. In the future, this can be
    replaced with HTTPProviderAdapter for microservice architecture.
    """
    
    def __init__(self, provider: TTSProvider):
        self.provider = provider
        self.name = provider.name

    def _build_voice_cfg(self, request: TTSRequest) -> Optional[Any]:
        if not request.voice_config:
            return None

        if request.voice_config.reference_audio:
            return ReplicatedVoiceConfig(
                reference_audio=request.voice_config.reference_audio,
                reference_text=request.voice_config.reference_text,
                enhance_speech=request.voice_config.enhance_speech or False,
                language=request.voice_config.language,
                volume=request.voice_config.volume,
                speed=request.voice_config.speed,
                pitch=request.voice_config.pitch,
                emotion=request.voice_config.emotion,
            )

        return VoiceConfig(
            voice_id=request.voice_config.voice_id,
            language=request.voice_config.language,
            volume=request.voice_config.volume,
            speed=request.voice_config.speed,
            emotion=request.voice_config.emotion,
            pitch=request.voice_config.pitch,
        )

    def _build_audio_cfg(self, request: TTSRequest) -> Optional[AudioConfig]:
        if not request.audio_config:
            return None
        return AudioConfig(
            encoding=request.audio_config.encoding,
            container=request.audio_config.container,
            bit_rate=request.audio_config.bit_rate,
            sample_rate=request.audio_config.sample_rate,
            channel=request.audio_config.channel,
        )

    def _resolve_voice_id(self, request: TTSRequest) -> Optional[str]:
        if request.voice_config and request.voice_config.voice_id:
            return request.voice_config.voice_id

        if hasattr(self.provider, 'default_voice_id'):
            return getattr(self.provider, 'default_voice_id', None)
        if hasattr(self.provider, 'supported_voices') and getattr(self.provider, 'supported_voices', None):
            sv = getattr(self.provider, 'supported_voices', None)
            if isinstance(sv, list) and len(sv) > 0:
                return sv[0]
        return None

    def _call_synthesize_compatible(
        self,
        *,
        text: str,
        output_file: Path,
        voice_cfg: Optional[Any],
        audio_cfg: Optional[AudioConfig],
        model: Optional[str],
        voice_id: str,
    ) -> bool:
        """Call provider.synthesize() across multiple legacy/new signatures."""

        try:
            return bool(
                self.provider.synthesize(
                    text=text,
                    output_file=output_file,
                    voice_config=voice_cfg if isinstance(voice_cfg, VoiceConfig) else None,
                    audio_config=audio_cfg,
                )
            )
        except TypeError:
            pass

        try:
            gen_voice_cfg = voice_cfg if isinstance(voice_cfg, VoiceConfig) else VoiceConfig(voice_id=None)
            generation_config = GenerateSpeechConfig(
                model=model or "",
                voice_config=gen_voice_cfg,
                audio_config=audio_cfg,
            )
            return bool(self.provider.synthesize(text=text, output_file=output_file, generation_config=generation_config))
        except TypeError:
            pass

        try:
            return bool(self.provider.synthesize(text, voice_id, output_file))
        except TypeError:
            pass

        return bool(self.provider.synthesize(text=text, voice=voice_id, output_file=output_file))
    
    async def synthesize(self, request: TTSRequest, output_dir: Path) -> TTSResponse:
        """
        Execute TTS synthesis using the provider.
        
        Args:
            request: TTSRequest with provider, text, voice_config, audio_config
            output_dir: Directory to save output audio file
            
        Returns:
            TTSResponse with success status and audio URL or error
        """
        try:
            # Generate output filename
            from datetime import datetime
            import re
            
            # Clean text for filename (first 30 chars, alphanumeric only)
            clean_text = re.sub(r'[^\w\s-]', '', request.text[:30]).strip().replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine file extension from audio_config
            container = request.audio_config.container if request.audio_config else "wav"
            ext = container if container else "wav"
            
            filename = f"{request.provider}_{clean_text}_{timestamp}.{ext}"
            output_file = output_dir / filename
            
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            voice_cfg = self._build_voice_cfg(request)
            audio_cfg = self._build_audio_cfg(request)
            resolved_voice_id = self._resolve_voice_id(request) or ""
            
            # Execute synthesis
            logger.info(f"Synthesizing with {request.provider}: '{request.text[:50]}...'")
            
            success = self._call_synthesize_compatible(
                text=request.text,
                output_file=output_file,
                voice_cfg=voice_cfg,
                audio_cfg=audio_cfg,
                model=request.model,
                voice_id=resolved_voice_id,
            )
            
            # Build response
            if success:
                # Get effective configs from provider if available
                eff_voice_cfg = {}
                eff_audio_cfg = {}
                
                if hasattr(self.provider, 'provider_config') and self.provider.provider_config:
                    provider_cfg = self.provider.provider_config
                    if hasattr(provider_cfg, 'default_model'):
                        eff_model = request.model or provider_cfg.default_model
                    else:
                        eff_model = request.model
                else:
                    eff_model = request.model
                
                # Try to get effective configs from provider attributes
                if hasattr(self.provider, 'default_voice_id'):
                    eff_voice_cfg['voice_id'] = self.provider.default_voice_id
                if hasattr(self.provider, 'language'):
                    eff_voice_cfg['language'] = self.provider.language
                if hasattr(self.provider, 'sample_rate'):
                    eff_audio_cfg['sample_rate'] = self.provider.sample_rate
                
                # Override with request configs if provided
                if request.voice_config:
                    if request.voice_config.voice_id:
                        eff_voice_cfg['voice_id'] = request.voice_config.voice_id
                    if request.voice_config.language:
                        eff_voice_cfg['language'] = request.voice_config.language
                    if request.voice_config.volume is not None:
                        eff_voice_cfg['volume'] = request.voice_config.volume
                    if request.voice_config.speed is not None:
                        eff_voice_cfg['speed'] = request.voice_config.speed
                    if request.voice_config.emotion:
                        eff_voice_cfg['emotion'] = request.voice_config.emotion
                
                if request.audio_config:
                    if request.audio_config.container:
                        eff_audio_cfg['container'] = request.audio_config.container
                    if request.audio_config.encoding:
                        eff_audio_cfg['encoding'] = request.audio_config.encoding
                    if request.audio_config.sample_rate:
                        eff_audio_cfg['sample_rate'] = request.audio_config.sample_rate
                
                return TTSResponse(
                    success=True,
                    text=request.text,
                    audio_url=str(output_file),
                    provider=request.provider,
                    model=eff_model,
                    effective_voice_config=eff_voice_cfg or None,
                    effective_audio_config=eff_audio_cfg or None,
                )
            else:
                # Get detailed error from provider if available
                error_detail = "Provider returned failure"
                if hasattr(self.provider, 'last_error') and self.provider.last_error:
                    error_detail = self.provider.last_error
                return TTSResponse(
                    success=False,
                    text=request.text,
                    audio_url=None,
                    provider=request.provider,
                    model=request.model,
                    error=TTSError(message="Synthesis failed", detail=error_detail)
                )
                
        except Exception as e:
            logger.error(f"Synthesis error with {request.provider}: {e}")
            return TTSResponse(
                success=False,
                text=request.text,
                audio_url=None,
                provider=request.provider,
                model=request.model,
                error=TTSError(message="Synthesis error", detail=str(e))
            )
    
    async def clone(self, request: TTSRequest, output_dir: Path) -> TTSResponse:
        """
        Execute voice cloning using the provider.
        
        Args:
            request: TTSRequest with provider, text, voice_config (must have reference_audio)
            output_dir: Directory to save output audio file
            
        Returns:
            TTSResponse with success status and audio URL or error
        """
        try:
            from datetime import datetime
            import re
            
            # Validate reference_audio exists
            if not request.voice_config or not request.voice_config.reference_audio:
                return TTSResponse(
                    success=False,
                    text=request.text,
                    audio_url=None,
                    provider=request.provider,
                    model=request.model,
                    error=TTSError(
                        message="Missing reference audio",
                        detail="Voice cloning requires voice_config.reference_audio to be provided"
                    )
                )
            
            # Check provider supports cloning
            if not hasattr(self.provider, 'clone_with_metadata'):
                return TTSResponse(
                    success=False,
                    text=request.text,
                    audio_url=None,
                    provider=request.provider,
                    model=request.model,
                    error=TTSError(
                        message="Voice cloning not supported",
                        detail=f"Provider '{request.provider}' does not support clone_with_metadata()"
                    )
                )
            
            # Generate output filename
            clean_text = re.sub(r'[^\w\s-]', '', request.text[:30]).strip().replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            container = request.audio_config.container if request.audio_config else "wav"
            ext = container if container else "wav"
            
            filename = f"{request.provider}_clone_{clean_text}_{timestamp}.{ext}"
            output_file = output_dir / filename
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build configs
            voice_cfg = self._build_voice_cfg(request)
            audio_cfg = self._build_audio_cfg(request)
            
            # Ensure we have ReplicatedVoiceConfig
            if not isinstance(voice_cfg, ReplicatedVoiceConfig):
                voice_cfg = ReplicatedVoiceConfig(
                    reference_audio=request.voice_config.reference_audio,
                    reference_text=request.voice_config.reference_text,
                    enhance_speech=request.voice_config.enhance_speech or True,
                    language=request.voice_config.language,
                    volume=request.voice_config.volume,
                    speed=request.voice_config.speed,
                    pitch=request.voice_config.pitch,
                    emotion=request.voice_config.emotion,
                )
            
            logger.info(f"🎭 Cloning with {request.provider}: '{request.text[:50]}...'")
            
            vc_job = VoiceCloningConfig(
                model=request.model or "",
                voice_config=voice_cfg,
                audio_config=audio_cfg,
            )
            
            clone_result = self.provider.clone_with_metadata(
                text=request.text,
                output_file=output_file,
                voice_cloning_config=vc_job,
            )
            
            # Handle SynthesisResult response
            if isinstance(clone_result, SynthesisResult):
                if clone_result.success:
                    return TTSResponse(
                        success=True,
                        text=request.text,
                        audio_url=clone_result.output_file,
                        provider=request.provider,
                        model=clone_result.model,
                        effective_voice_config=clone_result.effective_voice_config,
                        effective_audio_config=clone_result.effective_audio_config,
                    )
                return TTSResponse(
                    success=False,
                    text=request.text,
                    audio_url=None,
                    provider=request.provider,
                    model=clone_result.model,
                    effective_voice_config=clone_result.effective_voice_config,
                    effective_audio_config=clone_result.effective_audio_config,
                    error=TTSError(
                        message=(clone_result.error or {}).get('message', 'Voice cloning failed'),
                        detail=(clone_result.error or {}).get('detail')
                    ),
                )
            
            # Handle dict response
            if isinstance(clone_result, dict):
                if clone_result.get('success'):
                    return TTSResponse(
                        success=True,
                        text=request.text,
                        audio_url=clone_result.get('output_file'),
                        provider=request.provider,
                        model=clone_result.get('model') or request.model,
                        effective_voice_config=clone_result.get('effective_voice_config'),
                        effective_audio_config=clone_result.get('effective_audio_config'),
                    )
                err = clone_result.get('error')
                msg = err.get('message') if isinstance(err, dict) else (err or 'Voice cloning failed')
                detail = err.get('detail') if isinstance(err, dict) else None
                return TTSResponse(
                    success=False,
                    text=request.text,
                    audio_url=None,
                    provider=request.provider,
                    model=clone_result.get('model') or request.model,
                    effective_voice_config=clone_result.get('effective_voice_config'),
                    effective_audio_config=clone_result.get('effective_audio_config'),
                    error=TTSError(message=msg, detail=detail),
                )
            
            # Get detailed error from provider if available
            error_detail = "Unexpected clone result type"
            if hasattr(self.provider, 'last_error') and self.provider.last_error:
                error_detail = self.provider.last_error
            return TTSResponse(
                success=False,
                text=request.text,
                audio_url=None,
                provider=request.provider,
                model=request.model,
                error=TTSError(message="Voice cloning failed", detail=error_detail)
            )
            
        except Exception as e:
            logger.error(f"Clone error with {request.provider}: {e}")
            return TTSResponse(
                success=False,
                text=request.text,
                audio_url=None,
                provider=request.provider,
                model=request.model,
                error=TTSError(message="Clone error", detail=str(e))
            )
    
    async def health_check(self) -> HealthStatus:
        """Check if provider is healthy."""
        try:
            # Simple health check: verify provider has required attributes
            if hasattr(self.provider, 'name') and hasattr(self.provider, 'supported_voices'):
                return HealthStatus(
                    provider=self.name,
                    status="healthy",
                    message="Provider initialized successfully"
                )
            return HealthStatus(
                provider=self.name,
                status="unhealthy",
                message="Provider missing required attributes"
            )
        except Exception as e:
            return HealthStatus(
                provider=self.name,
                status="unhealthy",
                message=f"Health check failed: {str(e)}"
            )
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider metadata information."""
        try:
            return self.provider.get_metadata_info()
        except Exception as e:
            logger.error(f"Error getting provider info: {e}")
            return {
                "name": self.name,
                "error": str(e)
            }


class ProviderRouter:
    """
    Router for managing and routing requests to TTS providers.
    
    Responsibilities:
    - Maintain provider registry
    - Route requests to appropriate provider
    - Provide provider health status
    - List available providers
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.factory = ProviderFactory()
        self._adapters: Dict[str, ProviderAdapter] = {}
        self._provider_configs: Dict[str, Any] = {}
        
        logger.info("ProviderRouter initialized")
    
    def register_provider(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a provider with the router.
        
        Args:
            name: Provider name (e.g., 'cartesia', 'gemini')
            config: Optional configuration for the provider
            
        Returns:
            True if registration successful
        """
        try:
            config = config or {}
            provider = self.factory.create_provider(name, config)
            adapter = DirectProviderAdapter(provider)
            self._adapters[name.lower()] = adapter
            self._provider_configs[name.lower()] = config
            logger.info(f"✅ Registered provider: {name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to register provider {name}: {e}")
            return False
    
    def register_providers_from_config(self, config_path: Path) -> Dict[str, bool]:
        """
        Register multiple providers from a YAML config file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dict mapping provider names to registration success status
        """
        results = {}
        try:
            providers = self.factory.create_providers_from_config(config_path)
            for name, provider in providers.items():
                try:
                    adapter = DirectProviderAdapter(provider)
                    self._adapters[name.lower()] = adapter
                    results[name] = True
                    logger.info(f"✅ Registered provider from config: {name}")
                except Exception as e:
                    results[name] = False
                    logger.error(f"❌ Failed to register {name}: {e}")
        except Exception as e:
            logger.error(f"Error loading providers from config: {e}")
        
        return results
    
    def get_provider(self, name: str) -> Optional[ProviderAdapter]:
        """Get provider adapter by name."""
        return self._adapters.get(name.lower())
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._adapters.keys())
    
    def list_available_provider_types(self) -> List[str]:
        """List all available provider types that can be registered."""
        return self.factory.list_available_providers()
    
    async def route_request(self, request: TTSRequest) -> TTSResponse:
        """
        Route a TTS request to the appropriate provider.
        
        Args:
            request: TTSRequest containing provider name and synthesis parameters
            
        Returns:
            TTSResponse with synthesis result or error
        """
        provider_name = request.provider.lower()
        adapter = self._adapters.get(provider_name)
        
        if not adapter:
            # Try to auto-register the provider
            logger.info(f"Provider {request.provider} not registered, attempting auto-registration...")
            if self.register_provider(request.provider):
                adapter = self._adapters.get(provider_name)
        
        if not adapter:
            available = self.list_available_provider_types()
            return TTSResponse(
                success=False,
                text=request.text,
                audio_url=None,
                provider=request.provider,
                model=request.model,
                error=TTSError(
                    message=f"Provider '{request.provider}' not available",
                    detail=f"Available providers: {available}"
                )
            )
        
        return await adapter.synthesize(request, self.output_dir)
    
    async def route_clone_request(self, request: TTSRequest) -> TTSResponse:
        """
        Route a voice cloning request to the appropriate provider.
        
        Args:
            request: TTSRequest containing provider name, text, and voice_config with reference_audio
            
        Returns:
            TTSResponse with cloning result or error
        """
        provider_name = request.provider.lower()
        adapter = self._adapters.get(provider_name)
        
        if not adapter:
            # Try to auto-register the provider
            logger.info(f"Provider {request.provider} not registered, attempting auto-registration...")
            if self.register_provider(request.provider):
                adapter = self._adapters.get(provider_name)
        
        if not adapter:
            available = self.list_available_provider_types()
            return TTSResponse(
                success=False,
                text=request.text,
                audio_url=None,
                provider=request.provider,
                model=request.model,
                error=TTSError(
                    message=f"Provider '{request.provider}' not available",
                    detail=f"Available providers: {available}"
                )
            )
        
        return await adapter.clone(request, self.output_dir)
    
    async def health_check(self, provider_name: Optional[str] = None) -> Dict[str, HealthStatus]:
        """
        Check health status of providers.
        
        Args:
            provider_name: Optional specific provider to check. If None, checks all.
            
        Returns:
            Dict mapping provider names to HealthStatus
        """
        results = {}
        
        if provider_name:
            adapter = self._adapters.get(provider_name.lower())
            if adapter:
                results[provider_name] = await adapter.health_check()
            else:
                results[provider_name] = HealthStatus(
                    provider=provider_name,
                    status="unknown",
                    message="Provider not registered"
                )
        else:
            for name, adapter in self._adapters.items():
                results[name] = await adapter.health_check()
        
        return results
    
    def get_provider_info(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata information about providers.
        
        Args:
            provider_name: Optional specific provider. If None, returns all.
            
        Returns:
            Dict with provider information
        """
        if provider_name:
            adapter = self._adapters.get(provider_name.lower())
            if adapter:
                return {provider_name: adapter.get_info()}
            return {provider_name: {"error": "Provider not registered"}}
        
        return {name: adapter.get_info() for name, adapter in self._adapters.items()}


__all__ = [
    "ProviderAdapter",
    "DirectProviderAdapter",
    "ProviderRouter",
]
