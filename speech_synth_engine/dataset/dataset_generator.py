#!/usr/bin/env python3
# ============================================================
# Dataset Generator
# Main engine for TTS generation with multi-provider support
# ============================================================

import time
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging
from tqdm import tqdm

# Import các thành phần đã tạo
from ..providers.base.provider_factory import ProviderFactory
from ..providers.base.provider import TTSProvider
from .directory_manager import DirectoryManager

@dataclass
class BaseGenerationResult:
    """Base class for generation results"""
    # Required fields (no default values)
    success: bool
    text: str
    provider: str
    model: str
    audio_path: Path
    metadata_path: Path
    duration: float
    
    # Optional fields (with default values)
    error: Optional[str] = None
    file_size: int = 0
    skipped_duplicate: bool = False  # Flag to indicate this was skipped as duplicate

@dataclass
class SynthesisResult(BaseGenerationResult):
    """Result of a single synthesis operation"""
    # Optional fields (with default values)
    voice: Optional[str] = None

@dataclass
class CloneResult(BaseGenerationResult):
    """Result of a single voice clone operation"""
    # Required fields (no default values)
    reference_audio: Optional[str] = None
    
    # Optional fields (with default values)
    clone_id: Optional[str] = None

@dataclass
class BatchGenerationSummary:
    """Summary of a batch generation"""
    total_texts: int
    successful_generations: int
    failed_generations: int
    total_duration: float
    errors: List[str]
    results: List[Union[SynthesisResult, CloneResult]]

class DatasetGenerator:
    """
    Dataset generator with multi-provider support, batch processing,
    and automatic directory structure management.
    """

    def __init__(self, output_dir: Path, providers_config: Dict[str, Any] = None,
                 config_file: Path = None):
        """
        Initialize Dataset Generator.

        Args:
            output_dir: Main output directory
            providers_config: Providers configuration (dict or from file)
            config_file: YAML config file (takes precedence over providers_config)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.provider_factory = ProviderFactory()
        self.directory_manager = DirectoryManager(self.output_dir)
        self.providers = {}
        self.logger = logging.getLogger("DatasetGenerator")

        # Load providers configuration
        if config_file and config_file.exists():
            self.providers = self.provider_factory.create_providers_from_config(config_file)
        elif providers_config:
            # Create providers from dict config
            for provider_name, config in providers_config.items():
                try:
                    provider = self.provider_factory.create_provider(provider_name, config)
                    self.providers[provider_name] = provider
                except Exception as e:
                    self.logger.error(f"❌ Error creating provider {provider_name}: {e}")

        if not self.providers:
            self.logger.warning("⚠️ No providers were initialized")

        self.logger.info(f"✅ DatasetGenerator initialized with {len(self.providers)} providers")

    def synthesize_from_text_list(self, 
                                 text_items: List[Tuple[str, str]],
                                 provider_model_voice_list: List[Tuple[str, str, str]],
                                 batch_size: int = 10,
                                 delay_between_requests: float = 2,
                                 continue_on_error: bool = True) -> BatchGenerationSummary:
        """
        Synthesize audio from text list with IDs using multiple providers.

        Args:
            text_items: List of (id, text) tuples to generate
            provider_model_voice_list: List of (provider, model, voice) combinations
            batch_size: Number of texts to process in each batch
            delay_between_requests: Delay between requests (seconds)
            continue_on_error: Continue if error occurs

        Returns:
            BatchGenerationSummary containing summary of results
        """
        if not text_items:
            raise ValueError("Empty text_items list")

        if not provider_model_voice_list:
            raise ValueError("Empty provider_model_voice list")

        self.logger.info(f"🚀 Starting synthesize generation with {len(text_items)} text items and {len(provider_model_voice_list)} provider configs")

        all_results = []
        errors = []
        total_start_time = time.time()

        try:
            # Process in batches to optimize memory and progress tracking
            for i in tqdm(range(0, len(text_items), batch_size), desc="Synthesizing batches"):
                batch_items = text_items[i:i+batch_size]

                for text_id, text in batch_items:
                    if not text.strip():
                        continue

                    # Generate with each provider combination
                    for provider_name, model, voice in provider_model_voice_list:
                        try:
                            result = self._generate_single_text(
                                text_id, text, provider_name, model, voice, "synthesize"
                            )

                            if result.success:
                                all_results.append(result)
                            else:
                                errors.append(f"Text '{text[:50]}...' (ID: {text_id}): {result.error}")
                                if not continue_on_error:
                                    raise Exception(f"Generation failed: {result.error}")

                        except Exception as e:
                            error_msg = f"Error with text '{text[:50]}...' (ID: {text_id}) and ({provider_name}, {model}, {voice}): {e}"
                            self.logger.error(f"❌ {error_msg}")
                            errors.append(error_msg)
                            if not continue_on_error:
                                raise

                        # Delay between requests to avoid rate limit
                        if delay_between_requests > 0:
                            time.sleep(delay_between_requests)

        except KeyboardInterrupt:
            self.logger.info("⏹️ Generation interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Critical error: {e}")
            errors.append(f"Critical error: {e}")

        # Calculate statistics
        total_duration = time.time() - total_start_time
        successful = len([r for r in all_results if r.success])
        failed = len(errors)

        summary = BatchGenerationSummary(
            total_texts=len(text_items),
            successful_generations=successful,
            failed_generations=failed,
            total_duration=total_duration,
            errors=errors,
            results=all_results
        )

        self._log_summary(summary)
        return summary

    def clone_from_text_list(self, 
                           text_items: List[Tuple[str, str]],
                           provider_model_voice_list: List[Tuple[str, str, str]],
                           reference_audio: Path,
                           batch_size: int = 10,
                           delay_between_requests: float = 2,
                           continue_on_error: bool = True) -> BatchGenerationSummary:
        """
        Clone voice from reference audio to text list with IDs using multiple providers.
        Optimized for MinimaxSeleniumProvider to reuse browser session.

        Args:
            text_items: List of (id, text) tuples to generate
            provider_model_voice_list: List of (provider, reference_filename, voice) combinations
            reference_audio: Path to reference audio file for cloning
            batch_size: Number of texts to process in each batch
            delay_between_requests: Delay between requests (seconds)
            continue_on_error: Continue if error occurs

        Returns:
            BatchGenerationSummary containing summary of results
        """
        if not reference_audio or not reference_audio.exists():
            raise ValueError("reference_audio is required and must exist for clone operations")
            
        if not text_items:
            raise ValueError("Empty text_items list")

        if not provider_model_voice_list:
            raise ValueError("Empty provider_model_voice list")

        self.logger.info(f"🚀 Starting clone generation with {len(text_items)} text items and {len(provider_model_voice_list)} provider configs")

        all_results = []
        errors = []
        total_start_time = time.time()

        try:
            # Group by provider to optimize browser sessions
            provider_groups = {}
            for provider_name, reference_filename, voice in provider_model_voice_list:
                if provider_name not in provider_groups:
                    provider_groups[provider_name] = []
                provider_groups[provider_name].append((reference_filename, voice))

            # Process each provider group
            for provider_name, ref_voice_pairs in provider_groups.items():
                provider = self.providers.get(provider_name)
                if not provider:
                    error_msg = f"Provider {provider_name} not found"
                    self.logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    if not continue_on_error:
                        raise ValueError(error_msg)
                    continue

                # Special handling for MinimaxSeleniumProvider
                is_selenium = hasattr(provider, 'is_selenium') and provider.is_selenium
                
                # Process in batches
                for i in tqdm(range(0, len(text_items), batch_size), desc=f"Cloning with {provider_name}"):
                    batch_items = text_items[i:i+batch_size]
                    
                    # For Selenium providers, process all texts in one go
                    if is_selenium:
                        try:
                            # Process all texts for this provider in one batch
                            for ref_filename, voice in ref_voice_pairs:
                                for text_id, text in batch_items:
                                    if not text.strip():
                                        continue
                                        
                                    result = self.clone_single_text(
                                        text_id=text_id,
                                        text=text,
                                        provider_name=provider_name,
                                        reference_audio=reference_audio,
                                        voice=voice,
                                        model=ref_filename
                                    )
                                    
                                    if result.success:
                                        all_results.append(result)
                                    else:
                                        error_msg = f"Text '{text[:50]}...' (ID: {text_id}): {result.error}"
                                        self.logger.error(f"❌ {error_msg}")
                                        errors.append(error_msg)
                                        if not continue_on_error:
                                            raise Exception(f"Generation failed: {result.error}")
                                    
                                    # Small delay between items
                                    if delay_between_requests > 0:
                                        time.sleep(delay_between_requests)
                        except Exception as e:
                            error_msg = f"Error with {provider_name}: {str(e)}"
                            self.logger.error(f"❌ {error_msg}")
                            errors.append(error_msg)
                            if not continue_on_error:
                                raise
                    else:
                        # Non-selenium providers (original behavior)
                        for text_id, text in batch_items:
                            if not text.strip():
                                continue
                                
                            for ref_filename, voice in ref_voice_pairs:
                                try:
                                    result = self.clone_single_text(
                                        text_id=text_id,
                                        text=text,
                                        provider_name=provider_name,
                                        reference_audio=reference_audio,
                                        voice=voice,
                                        model=ref_filename
                                    )

                                    if result.success:
                                        all_results.append(result)
                                    else:
                                        error_msg = f"Text '{text[:50]}...' (ID: {text_id}): {result.error}"
                                        self.logger.error(f"❌ {error_msg}")
                                        errors.append(error_msg)
                                        if not continue_on_error:
                                            raise Exception(f"Generation failed: {result.error}")

                                    # Delay between requests to avoid rate limit
                                    if delay_between_requests > 0:
                                        time.sleep(delay_between_requests)
                                        
                                except Exception as e:
                                    error_msg = f"Error with text '{text[:50]}...' (ID: {text_id}) and ({provider_name}, {ref_filename}, {voice}): {e}"
                                    self.logger.error(f"❌ {error_msg}")
                                    errors.append(error_msg)
                                    if not continue_on_error:
                                        raise

        except KeyboardInterrupt:
            self.logger.info("⏹️ Generation interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Critical error: {e}")
            errors.append(f"Critical error: {e}")

        # Calculate statistics
        total_duration = time.time() - total_start_time
        successful = len([r for r in all_results if r.success])
        failed = len(errors)

        summary = BatchGenerationSummary(
            total_texts=len(text_items),
            successful_generations=successful,
            failed_generations=failed,
            total_duration=total_duration,
            errors=errors,
            results=all_results
        )

        self._log_summary(summary)
        return summary

    def generate_from_text_list(self, 
                              text_items: List[Tuple[str, str]],
                              provider_model_voice_list: List[Tuple[str, str, str]],
                              batch_size: int = 10,
                              delay_between_requests: float = 2,
                              continue_on_error: bool = True,
                              tts_type: str = "synthesize",
                              reference_audio: Optional[Path] = None) -> BatchGenerationSummary:
        """
        Generate audio from text list with IDs using multiple providers.
        This is a convenience method that routes to either synthesize_from_text_list or clone_from_text_list.
        
        Args:
            text_items: List of (id, text) tuples to generate
            provider_model_voice_list: List of (provider, model/voice, voice) combinations for synthesis
                                      or (provider, reference_filename, voice) for cloning
            batch_size: Number of texts to process in each batch (default: 10)
            delay_between_requests: Delay between requests in seconds (default: 0.5)
            continue_on_error: Whether to continue processing if an error occurs (default: True)
            tts_type: Type of operation - "synthesize" or "clone" (default: "synthesize")
            reference_audio: Required for clone operations, path to reference audio file (default: None)

        Returns:
            BatchGenerationSummary: Object containing summary of the generation results
            
        Raises:
            ValueError: If tts_type is invalid or reference_audio is missing for clone operations
            
        Example:
            # For synthesis
            generator.generate_from_text_list(
                [("id1", "Hello"), ("id2", "World")],
                [("gtts", "default", "en"), ("azure", "neural", "en-US")],
                tts_type="synthesize"
            )
            
            # For cloning
            generator.generate_from_text_list(
                [("id1", "Hello"), ("id2", "World")],
                [("minimax", "speaker1", "cloned_voice")],
                tts_type="clone",
                reference_audio=Path("path/to/reference.wav")
            )
        """
        # Input validation
        if not text_items:
            self.logger.warning("No text items provided for generation")
            return BatchGenerationSummary(
                total_texts=0,
                successful_generations=0,
                failed_generations=0,
                total_duration=0.0,
                errors=[],
                results=[]
            )
            
        if not provider_model_voice_list:
            raise ValueError("At least one provider configuration must be provided")
            
        tts_type = tts_type.lower()
        if tts_type not in ["synthesize", "clone"]:
            raise ValueError(f"Invalid tts_type: {tts_type}. Must be 'synthesize' or 'clone'")
            
        if tts_type == "clone" and reference_audio is None:
            raise ValueError("reference_audio is required for clone operations")
            
        if tts_type == "clone" and not reference_audio.exists():
            raise FileNotFoundError(f"Reference audio file not found: {reference_audio}")
        
        self.logger.info(f"Starting {tts_type} operation for {len(text_items)} text items with {len(provider_model_voice_list)} provider configurations")
        
        # Route to the appropriate method
        if tts_type == "synthesize":
            return self.synthesize_from_text_list(
                text_items=text_items,
                provider_model_voice_list=provider_model_voice_list,
                batch_size=batch_size,
                delay_between_requests=delay_between_requests,
                continue_on_error=continue_on_error
            )
        else:  # clone
            return self.clone_from_text_list(
                text_items=text_items,
                provider_model_voice_list=provider_model_voice_list,
                reference_audio=reference_audio,
                batch_size=batch_size,
                delay_between_requests=delay_between_requests,
                continue_on_error=continue_on_error
            )

    def synthesize_single_text(self, text_id: str, text: str, provider_name: str,
                             model: str, voice: str) -> SynthesisResult:
        """Synthesize audio for a single text using a specific provider
        
        Args:
            text_id: Unique identifier for the text
            text: Text to be converted to speech
            provider_name: Name of the TTS provider
            model: Model name to use for synthesis
            voice: Voice name to use for synthesis
            
        Returns:
            SynthesisResult containing the result of the synthesis operation
        """
        provider = self.providers.get(provider_name)
        if not provider:
            return SynthesisResult(
                success=False,
                text=text,
                provider=provider_name,
                model=model,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                voice=voice,
                error=f"Provider {provider_name} is not available"
            )

        try:
            # Create directory structure for synthesis
            wav_dir, metadata_file = self.directory_manager.create_output_directory(
                provider_name, model, voice
            )

            # Create file name using text_id from input
            safe_text = self._sanitize_filename(text[:50])
            audio_filename = f"{text_id}_{safe_text}.wav"
            audio_path = wav_dir / audio_filename

            # Check if file already exists - skip generation if it does
            if audio_path.exists():
                self.logger.info(f"⚠️ Audio file already exists: {audio_path}")
                # Add to metadata
                self.directory_manager.add_metadata_entry(
                    metadata_file=metadata_file,
                    text=text,
                    audio_path=audio_path.relative_to(self.directory_manager.base_dir),
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    tts_type="synthesize",
                    sample_rate=provider.sample_rate,
                    duration=0,  # Will be updated after synthesis
                    text_id=text_id
                )
                
                return SynthesisResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=0,
                    file_size=audio_path.stat().st_size,
                    voice=voice,
                    skipped_duplicate=True
                )

            # Generate the audio
            synth_result = provider.synthesize_with_metadata(text, voice, audio_path)

            if synth_result['success']:
                # Add to metadata
                self.directory_manager.add_metadata_entry(
                    metadata_file=metadata_file,
                    text=text,
                    audio_path=audio_path.relative_to(self.directory_manager.base_dir),
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    tts_type="synthesize",
                    sample_rate=provider.sample_rate,
                    duration=synth_result.get('estimated_duration', 0),
                    text_id=text_id
                )

                return SynthesisResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=synth_result.get('estimated_duration', 0),
                    file_size=audio_path.stat().st_size if audio_path.exists() else 0,
                    voice=voice
                )
            else:
                return SynthesisResult(
                    success=False,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=0,
                    voice=voice,
                    error=synth_result.get('error', 'Unknown error during synthesis')
                )

        except Exception as e:
            return SynthesisResult(
                success=False,
                text=text,
                provider=provider_name,
                model=model,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                voice=voice,
                error=f"Error during synthesis: {str(e)}"
            )

    def clone_single_text(self, text_id: str, text: str, provider_name: str,
                         reference_audio: str, voice: str, model: str = None) -> CloneResult:
        """Clone voice for a single text using a specific provider
        
        Args:
            text_id: Unique identifier for the text
            text: Text to be converted to speech
            provider_name: Name of the TTS provider
            reference_audio: Path to the reference audio file for cloning
            voice: Name of the voice to use
            model: Optional model name (defaults to reference_audio filename if not provided)
            
        Returns:
            CloneResult containing the result of the cloning operation
        """
        provider = self.providers.get(provider_name)
        model = model or Path(reference_audio).name if reference_audio else ""
        
        if not provider:
            return CloneResult(
                success=False,
                text=text,
                provider=provider_name,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                model=model,
                reference_audio=reference_audio,
                error=f"Provider {provider_name} is not available"
            )

        try:
            # Create output directory
            wav_dir, metadata_file = self.directory_manager.create_output_directory(
                provider_name, model, voice
            )

            # Create file name using text_id from input
            safe_text = self._sanitize_filename(text[:50])
            audio_filename = f"{text_id}_{safe_text}.wav"
            audio_path = wav_dir / audio_filename

            # Check if file already exists - skip generation if it does
            if audio_path.exists():
                self.logger.info(f"⚠️ Audio file already exists: {audio_path}")
                return CloneResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=0,
                    file_size=audio_path.stat().st_size,
                    model=model,
                    reference_audio=reference_audio,
                    skipped_duplicate=True,
                    clone_id=str(hash(reference_audio))  # Simple hash as clone_id
                )

            # Generate the audio using clone with reference_audio
            synth_result = provider.clone_with_metadata(text, reference_audio, audio_path)

            if synth_result['success']:
                # Add to metadata
                self.directory_manager.add_metadata_entry_clone(
                    metadata_file=metadata_file,
                    text=text,
                    audio_path=audio_path.relative_to(self.directory_manager.base_dir),
                    provider=provider_name,
                    reference_audio=reference_audio,
                    tts_type="clone",
                    sample_rate=provider.sample_rate,
                    duration=synth_result.get('estimated_duration', 0),
                    text_id=text_id,
                    audio_url=synth_result.get('audio_url', ""),
                    clone_id=synth_result.get('clone_id', "")
                )

                return CloneResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=synth_result.get('estimated_duration', 0),
                    file_size=audio_path.stat().st_size if audio_path.exists() else 0,
                    model=model,
                    reference_audio=reference_audio,
                    clone_id=synth_result.get('clone_id')
                )
            else:
                return CloneResult(
                    success=False,
                    text=text,
                    provider=provider_name,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=0,
                    model=model,
                    reference_audio=reference_audio,
                    error=synth_result.get('error', 'Unknown error during cloning')
                )

        except Exception as e:
            return CloneResult(
                success=False,
                text=text,
                provider=provider_name,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                model=model,
                reference_audio=reference_audio,
                error=f"Error during cloning: {str(e)}"
            )

    def _generate_single_text(self, text_id: str, text: str, provider_name: str,
                            model: str, voice: str, tts_type: str = "synthesize") -> Union[SynthesisResult, CloneResult]:
        """Legacy method - use synthesize_single_text or clone_single_text directly
        
        Args:
            text_id: Unique identifier for the text
            text: Text to be converted to speech
            provider_name: Name of the TTS provider
            model: Model name or reference audio path (for clone)
            voice: Voice name (for synthesis)
            tts_type: Type of operation - "synthesize" or "clone"
            
        Returns:
            Either a SynthesisResult or CloneResult depending on the operation type
        """
        if tts_type == "clone":
            return self.clone_single_text(text_id, text, provider_name, model, voice)
        return self.synthesize_single_text(text_id, text, provider_name, model, voice)

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text to create a valid file name"""
        import re

        # Remove special characters and whitespace
        sanitized = re.sub(r'[<>:"/\\|?*]', '', text)
        sanitized = re.sub(r'\s+', '_', sanitized.strip())

        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + "..."

        return sanitized

    def _log_summary(self, summary: BatchGenerationSummary, skipped_duplicates: int = 0):
        """Log summary of generation results"""
        self.logger.info("📊 Generation Summary:")
        self.logger.info(f"   Total texts: {summary.total_texts}")
        self.logger.info(f"   ✅ Successful generations: {summary.successful_generations}")
        self.logger.info(f"   ⏭️ Skipped duplicates: {skipped_duplicates}")
        self.logger.info(f"   ❌ Failed generations: {summary.failed_generations}")
        self.logger.info(f"   ⏱️ Total duration: {summary.total_duration:.2f}s")
        self.logger.info(f"   📁 Output dir: {self.output_dir}")

        if summary.errors:
            self.logger.warning(f"⚠️ {len(summary.errors)} errors during generation")

        # Log a few errors if any
        if summary.errors:
            self.logger.info("🔍 A few errors detected:")
            for error in summary.errors[:3]:
                self.logger.info(f"   ❌ {error}")

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get overall statistics of the generation process"""
        return self.directory_manager.get_structure_summary()

    def validate_generation(self, provider: str = None, model_or_reference: str = None,
                          voice: str = None, tts_type: str = "synthesize") -> Dict[str, Any]:
        """Validate the integrity of generation results"""
        if provider:
            return self.directory_manager.validate_structure(provider, model_or_reference or "", voice or "", tts_type)
        else:
            return self.directory_manager.get_structure_summary()

    def cleanup_providers(self):
        """Cleanup all providers"""
        self.provider_factory.cleanup_all_providers()
        self.providers.clear()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup_providers()


# Convenience function to use easily
def generate_vietnamese_addresses(output_dir: Path, texts: List[str],
                                providers_config: Dict[str, Any] = None,
                                **kwargs) -> BatchGenerationSummary:
    """
    Convenience function to generate Vietnamese addresses.

    Args:
        output_dir: Thư mục output
        texts: Danh sách địa chỉ cần generate
        providers_config: Cấu hình providers
        **kwargs: Các tham số khác cho generation (tts_type, reference_audio, etc.)

    Returns:
        BatchGenerationSummary
    """
    generator = DatasetGenerator(output_dir, providers_config)

    # Mặc định sử dụng GTTS nếu không có config
    if not providers_config:
        default_config = {
            "gtts": {
                "sample_rate": 22050,
                "language": "vi"
            }
        }
        generator = DatasetGenerator(output_dir, default_config)

    # Mặc định provider_model_voice_list cho GTTS
    provider_model_voice_list = kwargs.get('provider_model_voice_list', [
        ("gtts", "default", "vi")
    ])

    return generator.generate_from_text_list(texts, provider_model_voice_list, **kwargs)
