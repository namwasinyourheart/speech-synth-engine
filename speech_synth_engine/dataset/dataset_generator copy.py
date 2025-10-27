#!/usr/bin/env python3
# ============================================================
# Dataset Generator
# Main engine for TTS generation with multi-provider support
# ============================================================

import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import logging
from tqdm import tqdm

# Import các thành phần đã tạo
from ..providers.base.provider_factory import ProviderFactory
from ..providers.base.provider import TTSProvider
from .directory_manager import DirectoryManager

@dataclass
class GenerationResult:
    """Result of a single generation"""
    success: bool
    text: str
    provider: str
    model: str
    voice: str
    audio_path: Path
    metadata_path: Path
    duration: float
    error: Optional[str] = None
    file_size: int = 0
    skipped_duplicate: bool = False  # Flag to indicate this was skipped as duplicate

@dataclass
class BatchGenerationSummary:
    """Summary of a batch generation"""
    total_texts: int
    successful_generations: int
    failed_generations: int
    total_duration: float
    errors: List[str]
    results: List[GenerationResult]

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

    def generate_from_text_list(self, text_items: List[Tuple[str, str]],
                              provider_model_voice_list: List[Tuple[str, str, str]],
                              batch_size: int = 10,
                              delay_between_requests: float = 0.5,
                              continue_on_error: bool = True) -> BatchGenerationSummary:
        """
        Generate audio from text list with IDs using multiple providers.

        Args:
            text_items: List of (id, text) tuples to generate
            provider_model_voice_list: List of (provider, model, voice) combinations to use
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

        self.logger.info(f"🚀 Starting generation with {len(text_items)} text items and {len(provider_model_voice_list)} provider configs")

        all_results = []
        errors = []
        total_start_time = time.time()

        try:
            # Process in batches to optimize memory and progress tracking
            for i in tqdm(range(0, len(text_items), batch_size), desc="Processing batches"):
                batch_items = text_items[i:i+batch_size]

                for text_id, text in batch_items:
                    if not text.strip():
                        continue

                    # Generate with each provider/model/voice combination
                    for provider_name, model, voice in provider_model_voice_list:
                        try:
                            result = self._generate_single_text(
                                text_id, text, provider_name, model, voice
                            )

                            if result.success:
                                all_results.append(result)
                            else:
                                errors.append(f"Text '{text[:50]}...' (ID: {text_id}): {result.error}")

                                if not continue_on_error:
                                    raise Exception(f"Generation failed: {result.error}")

                        except Exception as e:
                            error_msg = f"Error with text '{text[:50]}...' (ID: {text_id}) and {provider_name}/{model}/{voice}: {e}"
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

    def _generate_single_text(self, text_id: str, text: str, provider_name: str,
                            model: str, voice: str) -> GenerationResult:
        """Generate audio for a single text using a specific provider"""

        provider = self.providers.get(provider_name)
        if not provider:
            return GenerationResult(
                success=False,
                text=text,
                provider=provider_name,
                model=model,
                voice=voice,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                error=f"Provider {provider_name} is not available"
            )

        try:
            # Create directory structure
            wav_dir, metadata_file = self.directory_manager.create_provider_structure(
                provider_name, model, voice
            )

            # Create file name using text_id from input
            safe_text = self._sanitize_filename(text[:50])  # Lấy 50 ký tự đầu
            audio_filename = f"{text_id}_{safe_text}.wav"
            audio_path = wav_dir / audio_filename

            # Check if file already exists - skip generation if it does
            if audio_path.exists():
                self.logger.info(f"⚠️ Audio file already exists: {audio_path}")
                return GenerationResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=0,  # We don't know the actual duration
                    file_size=audio_path.stat().st_size if audio_path.exists() else 0,
                    skipped_duplicate=True  # Flag to indicate this was skipped as duplicate
                )

            # Synthesize with enhanced provider
            synth_result = provider.synthesize_with_metadata(text, voice, audio_path)

            if synth_result['success']:
                # Add to metadata with both utt_id and text_id
                self.directory_manager.add_metadata_entry(
                    metadata_file=metadata_file,
                    text=text,
                    audio_path=audio_path.relative_to(self.directory_manager.base_dir),
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    sample_rate=provider.sample_rate,
                    duration=synth_result.get('estimated_duration', 0),
                    text_id=text_id  # Add text_id from input
                )

                return GenerationResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=synth_result['estimated_duration'],
                    file_size=synth_result.get('file_info', {}).get('file_size', 0)
                )
            else:
                return GenerationResult(
                    success=False,
                    text=text,
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    audio_path=audio_path,
                    metadata_path=metadata_file,
                    duration=0,
                    error=synth_result.get('error', 'Unknown error')
                )

        except Exception as e:
            return GenerationResult(
                success=False,
                text=text,
                provider=provider_name,
                model=model,
                voice=voice,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                error=str(e)
            )

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

    def validate_generation(self, provider: str = None, model: str = None,
                          voice: str = None) -> Dict[str, Any]:
        """Validate the integrity of generation results"""
        if provider:
            return self.directory_manager.validate_structure(provider, model or "", voice or "")
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
        **kwargs: Các tham số khác cho generation

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
