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
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

# Import các thành phần đã tạo
from ..providers.base.provider_factory import ProviderFactory
from ..providers.base.provider import TTSProvider
from ..schemas.provider import ProviderConfig, VoiceConfig, AudioConfig, ReplicatedVoiceConfig
from ..schemas.generation import GenerateSpeechConfig, VoiceCloningConfig
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

    def __init__(
        self, 
        output_dir: str | Path, 
        providers_config: Dict[str, Any] = None,
        config_file: Path = None,
        use_rich: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Initialize Dataset Generator.

        Args:
            output_dir: Main output directory (str or Path)
            providers_config: Providers configuration (dict or from file)
            config_file: YAML config file (takes precedence over providers_config)
        """
        self.output_dir = Path(output_dir) if not isinstance(output_dir, Path) else output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.provider_factory = ProviderFactory()
        self.directory_manager = DirectoryManager(self.output_dir)
        self.providers = {}
        self.logger = logging.getLogger("DatasetGenerator")
        self.use_rich = use_rich
        self.verbose = verbose
        self.console = Console() if use_rich else None
        
        # Setup file logging
        log_file = self.output_dir / "generation.log"
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent propagation to root logger to avoid console spam
        self.logger.propagate = False

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

        if self.use_rich:
            if not self.providers:
                self.console.print("[dim]ℹ️ No providers initialized. Will auto-create when needed.[/dim]")
            else:
                self.console.print(f"[green]✅ DatasetGenerator initialized with {len(self.providers)} provider(s)[/green]")
        
        self.logger.debug(f"DatasetGenerator initialized with {len(self.providers)} provider(s), output_dir={self.output_dir}")

    def _process_batch(self,
                      text_items: List[Tuple[str, str]],
                      process_fn,
                      batch_size: int = 10,
                      delay_between_requests: float = 2,
                      continue_on_error: bool = True,
                      rich_desc: str = None,
                      enable_concurrency: bool = False,
                      max_workers: int = 4) -> Tuple[list, list]:
        """Generic batch processing with error handling and delay. Optional concurrency."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        all_results = []
        errors = []
        try:
            for i in tqdm(range(0, len(text_items), batch_size), desc=rich_desc or "Processing batches"):
                batch_items = text_items[i:i+batch_size]
                if enable_concurrency:
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_to_item = {executor.submit(process_fn, text_id, text): (text_id, text) for text_id, text in batch_items if text.strip()}
                        for future in as_completed(future_to_item):
                            text_id, text = future_to_item[future]
                            try:
                                result = future.result()
                                if result.success:
                                    all_results.append(result)
                                else:
                                    self._handle_generation_error(errors, f"Text '{text[:50]}...' (ID: {text_id}): {result.error}", continue_on_error)
                            except Exception as e:
                                self._handle_generation_error(errors, f"Error with text '{text[:50]}...' (ID: {text_id}): {e}", continue_on_error)
                            if delay_between_requests > 0:
                                time.sleep(delay_between_requests)
                else:
                    for text_id, text in batch_items:
                        if not text.strip():
                            continue
                        try:
                            result = process_fn(text_id, text)
                            if result.success:
                                all_results.append(result)
                            else:
                                self._handle_generation_error(errors, f"Text '{text[:50]}...' (ID: {text_id}): {result.error}", continue_on_error)
                        except Exception as e:
                            self._handle_generation_error(errors, f"Error with text '{text[:50]}...' (ID: {text_id}): {e}", continue_on_error)
                        if delay_between_requests > 0:
                            time.sleep(delay_between_requests)
        except KeyboardInterrupt:
            self.logger.info("⏹️ Generation interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Critical error: {e}")
            errors.append(f"Critical error: {e}")
        return all_results, errors

    def _handle_generation_error(self, errors: list, error_msg: str, continue_on_error: bool):
        self.logger.error(f"❌ {error_msg}")
        errors.append(error_msg)
        if not continue_on_error:
            raise Exception(error_msg)

    def synthesize_from_text_list(self, 
                                 text_items: List[Tuple[str, str]],
                                 provider_model_voice: Tuple[str, str, str],
                                 batch_size: int = 10,
                                 delay_between_requests: float = 2,
                                 continue_on_error: bool = True,
                                 generation_config: Optional[GenerateSpeechConfig] = None
                                 ) -> BatchGenerationSummary:
        """
        Synthesize audio from text list with IDs using a single provider configuration.

        Args:
            text_items: List of (id, text) tuples to generate
            provider_model_voice: A tuple of (provider, model, voice)
            batch_size: Number of texts to process in each batch
            delay_between_requests: Delay between requests (seconds)
            continue_on_error: Continue if error occurs

        Returns:
            BatchGenerationSummary containing summary of results
        """
        if not text_items:
            raise ValueError("Empty text_items list")


        provider_name, model, voice = provider_model_voice
        self.logger.info(f"🚀 Starting synthesize generation with {len(text_items)} text items using provider {provider_name} (model: {model}, voice: {voice})")

        total_start_time = time.time()
        provider_name, model, voice = provider_model_voice
        def synth_fn(text_id, text):
            return self._generate_single_text(
                text_id, text, provider_name, model, voice, "synthesize", generation_config=generation_config
            )
        all_results, errors = self._process_batch(
            text_items,
            synth_fn,
            batch_size=batch_size,
            delay_between_requests=delay_between_requests,
            continue_on_error=continue_on_error,
            rich_desc="Synthesizing batches"
        )
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

    # Removed synthesize_from_text_list_config: superseded by generate_from_configs()

    def clone_from_text_list(self, 
                           text_items: List[Tuple[str, str]],
                           provider_model_voice: Tuple[str, str, str],
                           reference_audio: Path,
                           batch_size: int = 10,
                           delay_between_requests: float = 2,
                           continue_on_error: bool = True
                           ) -> BatchGenerationSummary:
        """
        Clone voice from reference audio for a list of texts using a single provider configuration.

        Args:
            text_items: List of (id, text) tuples to generate.
            provider_model_voice: A tuple of (provider, model, voice).
            reference_audio: Path to the reference audio file for cloning.
            batch_size: Number of texts to process in each batch.
            delay_between_requests: Delay between requests in seconds.
            continue_on_error: Continue if an error occurs.

        Returns:
            A summary of the batch generation results.
        """
        if reference_audio is not None and not isinstance(reference_audio, Path):
            reference_audio = Path(reference_audio)
        if not reference_audio or not reference_audio.exists():
            raise ValueError("Reference audio is required and must exist for clone operations")
        if not text_items:
            raise ValueError("Empty text_items list")

        provider_name, model, voice = provider_model_voice
        self.logger.info(f"🚀 Starting clone generation with {len(text_items)} text items for provider '{provider_name}'")


        total_start_time = time.time()
        provider_name, model, voice = provider_model_voice
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")
        def clone_fn(text_id, text):
            return self.clone_single_text(
                text_id=text_id,
                text=text,
                provider_name=provider_name,
                reference_audio=reference_audio,
                voice=voice,
                model=model
            )
        all_results, errors = self._process_batch(
            text_items,
            clone_fn,
            batch_size=batch_size,
            delay_between_requests=delay_between_requests,
            continue_on_error=continue_on_error,
            rich_desc=f"Cloning with {provider_name}"
        )
        total_duration = time.time() - total_start_time
        summary = BatchGenerationSummary(
            total_texts=len(text_items),
            successful_generations=len([r for r in all_results if r.success]),
            failed_generations=len(errors),
            total_duration=total_duration,
            errors=errors,
            results=all_results
        )
        self._log_summary(summary)
        return summary

    def generate_from_text_list(self, 
                              text_items: List[Tuple[str, str]],
                              provider_model_voice: Tuple[str, str, str],
                              batch_size: int = 10,
                              delay_between_requests: float = 3,
                              continue_on_error: bool = True,
                              tts_type: str = "synthesize",
                              reference_audio: Optional[Path] = None,
                              generation_config: Optional[GenerateSpeechConfig] = None
                              ) -> BatchGenerationSummary:
        """
        Generate audio from text list with IDs using a single provider.
        This is a convenience method that routes to either synthesize_from_text_list or clone_from_text_list.
        
        Args:
            text_items: List of (id, text) tuples to generate
            provider_model_voice: A tuple of (provider, model, voice) for synthesis or cloning
            batch_size: Number of texts to process in each batch (default: 10)
            delay_between_requests: Delay between requests in seconds (default: 3.0)
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
                ("gtts", "default", "en"),
                tts_type="synthesize"
            )
            
            # For cloning
            generator.generate_from_text_list(
                [("id1", "Hello"), ("id2", "World")],
                ("minimax", "speaker1", "cloned_voice"),
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
            
        if not provider_model_voice:
            raise ValueError("Provider configuration must be provided")
            
        if len(provider_model_voice) != 3:
            raise ValueError("provider_model_voice must be a tuple of (provider, model, voice)")
            
        tts_type = tts_type.lower()
        if tts_type not in ["synthesize", "clone"]:
            raise ValueError(f"Invalid tts_type: {tts_type}. Must be 'synthesize' or 'clone'")
            
        if tts_type == "clone" and reference_audio is None:
            raise ValueError("reference_audio is required for clone operations")
            
        if tts_type == "clone" and not reference_audio.exists():
            raise FileNotFoundError(f"Reference audio file not found: {reference_audio}")
        
        self.logger.info(f"Starting {tts_type} operation for {len(text_items)} text items with provider configuration {provider_model_voice}")
        
        # Route to the appropriate method
        if tts_type == "synthesize":
            return self.synthesize_from_text_list(
                text_items=text_items,
                provider_model_voice=provider_model_voice,
                batch_size=batch_size,
                delay_between_requests=delay_between_requests,
                continue_on_error=continue_on_error,
                generation_config=generation_config,
            )
        else:  # clone
            return self.clone_from_text_list(
                text_items=text_items,
                provider_model_voice=provider_model_voice,
                reference_audio=reference_audio,
                batch_size=batch_size,
                delay_between_requests=delay_between_requests,
                continue_on_error=continue_on_error
            )

    def generate_from_configs(self,
                              text_items: List[Tuple[str, str]],
                              provider_config: ProviderConfig,
                              generation_config: Union[GenerateSpeechConfig, VoiceCloningConfig],
                              batch_size: int = 10,
                              delay_between_requests: float = 3,
                              continue_on_error: bool = True,
                              tts_type: str = "synthesize",
                              reference_audio: Optional[Path] = None,
                              enable_concurrency: bool = False,
                              max_workers: int = 4
                              ) -> BatchGenerationSummary:
        """
        Generate audio using ProviderConfig and GenerateSpeechConfig/VoiceCloningConfig.

        Behavior:
        - If the provider named in ProviderConfig is not initialized yet, this method
          will auto-create it using ProviderFactory and add it to self.providers.
        - Runs the internal batch flow directly via _generate_from_configs_batch(),
          threading GenerateSpeechConfig/VoiceCloningConfig to the provider where supported, and using
          (provider, model, voice) to organize output directories and metadata.
        """
        if generation_config is None or provider_config is None:
            raise ValueError("Both provider_config and generation_config are required")

        provider_name = provider_config.name
        model = generation_config.model
        
        # Extract voice identifier for directory naming
        # For VoiceCloningConfig with ReplicatedVoiceConfig, use a placeholder
        voice_cfg = generation_config.voice_config
        if hasattr(voice_cfg, 'voice_id'):
            voice = voice_cfg.voice_id
        elif hasattr(voice_cfg, 'reference_audio'):
            # For cloning, use a derived name from reference audio or default
            ref_audio = getattr(voice_cfg, 'reference_audio', None)
            if ref_audio:
                voice = Path(ref_audio).stem  # Use filename without extension
            else:
                voice = "cloned_voice"
        else:
            voice = "default_voice"

        # Ensure provider exists; if not, create it from ProviderConfig
        if provider_name not in self.providers:
            try:
                # Build a minimal config dict for provider creation
                cfg: Dict[str, Any] = {
                    'provider_config': provider_config.model_dump()
                }
                # Optionally carry model and sample_rate from GenerateSpeechConfig
                if model:
                    cfg['model'] = model
                audio_cfg = getattr(generation_config, 'audio_config', None)
                if audio_cfg and getattr(audio_cfg, 'sample_rate', None):
                    cfg['sample_rate'] = audio_cfg.sample_rate

                provider_instance = self.provider_factory.create_provider(provider_name, cfg)
                self.providers[provider_name] = provider_instance
                self.logger.debug(f"Auto-created provider '{provider_name}' from ProviderConfig")
            except Exception as e:
                raise ValueError(f"Failed to auto-create provider '{provider_name}': {e}")

        # Extract reference_audio from VoiceCloningConfig if not explicitly provided
        if reference_audio is None and tts_type == "clone":
            if hasattr(voice_cfg, 'reference_audio'):
                reference_audio = Path(voice_cfg.reference_audio)

        return self._generate_from_configs_batch(
            text_items=text_items,
            provider_name=provider_name,
            model=model,
            voice=voice,
            batch_size=batch_size,
            delay_between_requests=delay_between_requests,
            continue_on_error=continue_on_error,
            tts_type=tts_type,
            reference_audio=reference_audio,
            generation_config=generation_config,
            enable_concurrency=enable_concurrency,
            max_workers=max_workers,
        )

    def _generate_from_configs_batch(
        self,
        text_items: List[Tuple[str, str]],
        provider_name: str,
        model: str,
        voice: str,
        batch_size: int = 10,
        delay_between_requests: float = 3,
        continue_on_error: bool = True,
        tts_type: str = "synthesize",
        reference_audio: Optional[Path] = None,
        generation_config: Optional[GenerateSpeechConfig] = None,
        enable_concurrency: bool = False,
        max_workers: int = 4,
    ) -> BatchGenerationSummary:
        """
        Internal batch generator that uses ProviderConfig + GenerateSpeechConfig directly
        without routing through generate_from_text_list.
        """
        if not text_items:
            return BatchGenerationSummary(
                total_texts=0,
                successful_generations=0,
                failed_generations=0,
                total_duration=0.0,
                errors=[],
                results=[]
            )

        tts_type = (tts_type or "synthesize").lower()
        if tts_type not in ("synthesize", "clone"):
            raise ValueError(f"Invalid tts_type: {tts_type}.")
        if tts_type == "clone":
            if reference_audio is None:
                raise ValueError("reference_audio is required for clone operations")
            if isinstance(reference_audio, (str, bytes)):
                reference_audio = Path(reference_audio)
            if not reference_audio.exists():
                raise FileNotFoundError(f"Reference audio file not found: {reference_audio}")

        self._log_generation_start(provider_name, model, voice, tts_type, text_items)

        all_results: List[Union[SynthesisResult, CloneResult]] = []
        errors: List[str] = []
        total_start_time = time.time()

        # Sử dụng _process_batch cho logic xử lý batch, concurrency
        def batch_fn(text_id, text):
            if tts_type == "synthesize":
                return self._generate_single_text(
                    text_id=text_id,
                    text=text,
                    provider_name=provider_name,
                    model=model,
                    voice=voice,
                    tts_type="synthesize",
                    generation_config=generation_config,
                )
            else:
                return self.clone_single_text(
                    text_id=text_id,
                    text=text,
                    provider_name=provider_name,
                    reference_audio=reference_audio,
                    voice=voice,
                    model=model,
                )
        all_results, errors = self._process_batch(
            text_items,
            batch_fn,
            batch_size=batch_size,
            delay_between_requests=delay_between_requests,
            continue_on_error=continue_on_error,
            rich_desc=f"{tts_type.title()} with {provider_name}",
            enable_concurrency=enable_concurrency,
            max_workers=max_workers,
        )
        summary = self._build_batch_summary(text_items, all_results, errors, total_start_time)
        self._log_summary(summary)
        return summary

    def _log_generation_start(self, provider_name: str, model: str, voice: str, tts_type: str, text_items: list):
        self.logger.debug(f"Starting {tts_type} generation: provider={provider_name}, model={model}, voice={voice}, items={len(text_items)}")
        if self.use_rich and self.console:
            self._print_generation_panel(provider_name, model, voice, tts_type, text_items)

    def _print_generation_panel(self, provider_name: str, model: str, voice: str, tts_type: str, text_items: list):
        panel_title = "Synthetic Audio Generation" if tts_type == "synthesize" else "Voice Cloning"
        start_panel = Panel(
            f"[cyan]Provider:[/cyan] {provider_name}\n"
            f"[cyan]Model:[/cyan] {model}\n"
            f"[cyan]Voice:[/cyan] {voice}\n"
            f"[cyan]Type:[/cyan] {tts_type}\n"
            f"[cyan]Items:[/cyan] {len(text_items)}",
            title=f"🚀 {panel_title}",
            border_style="green",
            expand=False
        )
        self.console.print(start_panel)

    def _build_batch_summary(self, text_items, all_results, errors, total_start_time):
        total_duration = time.time() - total_start_time
        successful = len([r for r in all_results if r.success])
        failed = len(errors)
        return BatchGenerationSummary(
            total_texts=len(text_items),
            successful_generations=successful,
            failed_generations=failed,
            total_duration=total_duration,
            errors=errors,
            results=all_results,
        )


    def synthesize_single_text(self, text_id: str, text: str, provider_name: str,
                             model: str, voice: str,
                             generation_config: Optional[GenerateSpeechConfig] = None
                             ) -> SynthesisResult:
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

        # Sanitize voice name - extract base voice name if it contains path separators
        # For cases like 'vi/shards/shard_0', we want to extract 'vi' (the first part)
        clean_voice = voice.split('/')[0] if '/' in voice else voice

        try:
            # Create directory structure for synthesis
            voice_dir, wav_dir = self.directory_manager.create_output_directory(
                provider_name, model, voice
            )

            # Determine desired container/extension from GenerateSpeechConfig.audio_config.container
            desired_ext = ".wav"
            try:
                container_val = None
                if generation_config and getattr(generation_config, 'audio_config', None):
                    container_val = getattr(generation_config.audio_config, 'container', None)
                if isinstance(container_val, str):
                    ext_map = {
                        'wav': '.wav',
                        'mp3': '.mp3',
                        # 'raw': '.raw',
                    }
                    desired_ext = ext_map.get(container_val.lower(), '.wav')
            except Exception:
                # Fallback to default .wav if anything unexpected happens
                desired_ext = ".wav"

            # Create file name using text_id from input
            safe_text = self._sanitize_filename(text[:50])
            audio_filename = f"{text_id}_{safe_text}{desired_ext}"
            audio_path = wav_dir / audio_filename
            self.logger.debug(f"Planned output audio path: {audio_path}")

            # Check if file already exists - skip generation if it does
            if audio_path.exists():
                self.logger.info(f"⚠️ Audio file already exists, skipping: {audio_path}")
                return SynthesisResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=voice_dir,  # Point to the directory
                    duration=0,
                    file_size=audio_path.stat().st_size,
                    voice=voice,
                    skipped_duplicate=True
                )

            # Prepare an effective GenerateSpeechConfig ensuring voice/model/sample_rate are set
            eff_gen_cfg = generation_config
            try:
                if eff_gen_cfg is None:
                    eff_gen_cfg = GenerateSpeechConfig(
                        model=model,
                        voice_config=VoiceConfig(voice_id=clean_voice),
                        audio_config=AudioConfig(channel=1, sample_rate=provider.sample_rate or 24000)
                    )
                else:
                    # Ensure model
                    if not getattr(eff_gen_cfg, 'model', None):
                        eff_gen_cfg.model = model
                    # Ensure voice
                    if getattr(eff_gen_cfg, 'voice_config', None) is None or not getattr(eff_gen_cfg.voice_config, 'voice_id', None):
                        eff_gen_cfg.voice_config = VoiceConfig(voice_id=clean_voice)
                    # Ensure sample_rate if missing
                    if getattr(eff_gen_cfg, 'audio_config', None) is None:
                        eff_gen_cfg.audio_config = AudioConfig(channel=1, sample_rate=provider.sample_rate or 24000)
                    elif getattr(eff_gen_cfg.audio_config, 'sample_rate', None) is None and provider.sample_rate:
                        eff_gen_cfg.audio_config.sample_rate = provider.sample_rate
            except Exception:
                # Fallback minimal config if anything goes wrong
                eff_gen_cfg = GenerateSpeechConfig(
                    model=model,
                    voice_config=VoiceConfig(voice_id=clean_voice),
                    audio_config=AudioConfig(channel=1, sample_rate=provider.sample_rate or 24000)
                )

            # Call provider synthesize_with_metadata with unified signature
            synth_result = provider.synthesize_with_metadata(text, audio_path, generation_config=eff_gen_cfg)

            if synth_result['success']:
                # Determine effective duration
                duration_val = None
                try:
                    if isinstance(synth_result, dict):
                        if synth_result.get('duration'):
                            duration_val = float(synth_result['duration'])
                        elif synth_result.get('estimated_duration'):
                            duration_val = float(synth_result['estimated_duration'])
                except Exception:
                    duration_val = None

                # If provider didn't return duration, calculate from the written file
                if duration_val is None or duration_val == 0:
                    duration_val = self.directory_manager._calculate_duration(audio_path)

                # Add metadata entry using the new method
                self.directory_manager.add_metadata_entry(
                    voice_dir=voice_dir,
                    text=text,
                    audio_path=audio_path,
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    tts_type="synthesize",
                    sample_rate=provider.sample_rate,
                    duration=duration_val,
                    text_id=text_id,
                    lang="vi"
                )

                return SynthesisResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=voice_dir,  # Point to the directory
                    duration=duration_val,
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
                    metadata_path=voice_dir,  # Point to the directory
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

    def clone_single_text(
        self, 
        text_id: str, 
        text: str, 
        provider_name: str,
        reference_audio: str, 
        voice: str, 
        model: str = None
    ) -> CloneResult:
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
                model=model,
                audio_path=Path(),
                metadata_path=Path(),
                duration=0,
                error=f"Provider {provider_name} is not available",
                file_size=0,
                skipped_duplicate=False,
                reference_audio=reference_audio,
            )

        try:
            # Create directory structure for cloning
            voice_dir, wav_dir = self.directory_manager.create_provider_structure_clone(
                provider_name, model, voice
            )

            # Create file name using text_id from input
            safe_text = self._sanitize_filename(text[:50])
            audio_filename = f"{text_id}_{safe_text}.wav"
            audio_path = wav_dir / audio_filename

            # Check if file already exists - skip generation if it does
            if audio_path.exists():
                self.logger.info(f"⚠️ Audio file already exists, skipping: {audio_path}")
                return CloneResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=voice_dir,  # Point to the directory
                    duration=0,
                    file_size=audio_path.stat().st_size,
                    reference_audio=reference_audio,
                    skipped_duplicate=True,
                )

            # Generate the audio using clone with VoiceCloningConfig compatible with Xiaomi provider
            try:
                vc_cfg = VoiceCloningConfig(
                    model=model or "OmniVoice",
                    voice_config=ReplicatedVoiceConfig(
                        reference_audio=str(reference_audio),
                        reference_text=None,
                        language="vi",
                    ),
                )
            except Exception:
                # Fallback minimal config in case dataclasses are unavailable
                vc_cfg = None

            if vc_cfg is not None:
                synth_result = provider.clone_with_metadata(
                    text,
                    audio_path,
                    voice_cloning_config=vc_cfg,
                )
            else:
                synth_result = provider.clone(text, audio_path)

            if synth_result['success']:
                # Determine effective duration
                duration_val = None
                try:
                    if isinstance(synth_result, dict):
                        if synth_result.get('duration'):
                            duration_val = float(synth_result['duration'])
                        elif synth_result.get('estimated_duration'):
                            duration_val = float(synth_result['estimated_duration'])
                except Exception:
                    duration_val = None

                # If provider didn't return duration, calculate from the written file
                if duration_val is None or duration_val == 0:
                    duration_val = self.directory_manager._calculate_duration(audio_path)

                # Add metadata entry using the new method
                self.directory_manager.add_metadata_entry_clone(
                    voice_dir=voice_dir,
                    text=text,
                    audio_path=audio_path,
                    provider=provider_name,
                    model=model,
                    voice=voice,
                    tts_type="clone",
                    sample_rate=provider.sample_rate,
                    duration=duration_val,
                    text_id=text_id,
                    lang="vi"
                )

                return CloneResult(
                    success=True,
                    text=text,
                    provider=provider_name,
                    model=model,
                    audio_path=audio_path,
                    metadata_path=voice_dir, # Point to the directory
                    duration=duration_val,
                    file_size=audio_path.stat().st_size if audio_path.exists() else 0,
                    reference_audio=reference_audio,
                )
            else:
                return CloneResult(
                    success=False,
                    text=text,
                    provider=provider_name,
                    audio_path=audio_path,
                    metadata_path=voice_dir, # Point to the directory
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
                            model: str, voice: str, tts_type: str = "synthesize",
                            generation_config: Optional[GenerateSpeechConfig] = None) -> Union[SynthesisResult, CloneResult]:
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
        return self.synthesize_single_text(text_id, text, provider_name, model, voice, generation_config=generation_config)

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

    def _save_text_items(self, text_items: List[Tuple[str, str]], output_path: Path):
        """Save text items to a file. Check if the file already exists before overwriting."""
        if output_path.exists():
            self.logger.warning(f"⚠️ Text items file already exists: {output_path}. Skipping save.")
            return
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                for text_id, text in text_items:
                    # Save as a string representation of a tuple
                    escaped_text = text.replace("'", "\\'")
                    f.write(f"('{text_id}', '{escaped_text}')\n")
            self.logger.info(f"✅ Saved {len(text_items)} text items to {output_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save text items to {output_path}: {e}")

    def _log_summary(self, summary: BatchGenerationSummary, skipped_duplicates: int = 0):
        """Log summary of generation results using Rich"""
        # Compute extras
        # Duration: sum of all audio durations
        total_audio_duration = 0.0
        try:
            total_audio_duration = sum(float(getattr(r, 'duration', 0) or 0) for r in (summary.results or []))
        except Exception:
            total_audio_duration = 0.0
        items_sec = (summary.total_texts / total_audio_duration) if total_audio_duration > 0 else 0.0
        total_size = 0
        try:
            total_size = sum(int(getattr(r, 'file_size', 0) or 0) for r in (summary.results or []))
        except Exception:
            total_size = 0

        # Create summary table
        table = Table(title="Generation Summary", show_header=True, header_style="bold", box=box.SQUARE, expand=True)
        table.add_column("Metric", style="white", width=22)
        table.add_column("Value", style="white", overflow="fold")
        
        table.add_row("Total Items", str(summary.total_texts))
        table.add_row("Success", f"{summary.successful_generations}")
        if skipped_duplicates > 0:
            table.add_row("Skipped", f"{skipped_duplicates}")
        if summary.failed_generations > 0:
            table.add_row("Failed", f"{summary.failed_generations}")
        table.add_row("Total Audio Duration", f"{total_audio_duration:.2f}s")
        if total_size > 0:
            table.add_row("Total Audio Size", f"{total_size/1024.0:.1f} KB")
        
        # Show full voice name if available
        if hasattr(self, 'voice_name') and self.voice_name:
            table.add_row("Voice Name", str(self.voice_name))
        table.add_row("Output Directory", str(self.output_dir))


        

        if self.use_rich and self.console:
            self.console.print(table)
        else:
            # Fallback plain logging
            self.logger.info("📊 Generation Summary")
            for row in table.rows:
                self.logger.info(" | ".join(cell.plain for cell in row.cells))

        # Show errors if any
        if summary.errors and self.use_rich and self.console:
            error_table = Table(title=f"⚠️ {len(summary.errors)} Error(s) Detected", show_header=True, header_style="bold red", box=box.SQUARE)
            error_table.add_column("#", style="red", width=4)
            error_table.add_column("Error", style="white")
            for i, error in enumerate(summary.errors[:10]):
                error_table.add_row(str(i+1), error)
            self.console.print(error_table)


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

    def cleanup_providers(self) -> None:
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
        output_dir: Output directory path
        texts: List of address texts to generate
        providers_config: Provider configurations
        **kwargs: Additional generation parameters (tts_type, reference_audio, etc.)
            - provider_model_voice: Tuple of (provider, model, voice) to use (default: ('gtts', 'default', 'vi'))

    Returns:
        BatchGenerationSummary containing generation results
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

    # Get provider_model_voice from kwargs or use default GTTS config
    provider_model_voice = kwargs.pop('provider_model_voice', ("gtts", "default", "vi"))
    
    # Convert text strings to (id, text) tuples if needed
    text_items = [(str(i), text) for i, text in enumerate(texts)]
    
    return generator.generate_from_text_list(
        text_items=text_items,
        provider_model_voice=provider_model_voice,
        **kwargs
    )
