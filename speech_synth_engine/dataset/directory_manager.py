#!/usr/bin/env python3
# ============================================================
# Directory Manager
# Manage directory structure and metadata for TTS generation
# ============================================================

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

class DirectoryManager:
    """
    Manage directory structure and metadata for TTS generation.
    Creates and maintains structure: provider/model/voice/wav/ with CSV metadata.
    """

    def __init__(self, base_output_dir: Path):
        self.base_dir = Path(base_output_dir)
        self.logger = logging.getLogger("DirectoryManager")

        # Define directory structure
        self.structure_template = {
            'provider': '',
            'model': '',
            'voice': '',
            'wav': 'wav',
            'metadata': 'metadata.tsv'  # Changed from .csv to .tsv
        }

    def create_output_directory(self, provider: str, model: str, voice: str) -> Tuple[Path, Path]:
        """
        Create directory structure for a specific provider/model/voice.

        Args:
            provider (str): Provider name (e.g., gtts, gemini, minimax, etc.)
            model (str): Model name (e.g., default, neural, etc.)
            voice (str): Voice name (e.g., vi, vi-VN-HoaiMyNeural, etc.)

        Returns:
            Tuple[Path, Path]: A tuple containing the path to the wav directory and the path to the metadata file.
        """
        try:
            # Create directory paths
            provider_dir = self.base_dir / provider
            model_dir = provider_dir / model
            voice_dir = model_dir / voice
            wav_dir = voice_dir / "wav"

            # Create necessary directories
            wav_dir.mkdir(parents=True, exist_ok=True)

            # Metadata file path
            metadata_file = voice_dir / "metadata.tsv"

            # Initialize metadata file with header if not exists
            self.initialize_metadata_file(metadata_file)

            self.logger.info(f"✅ Directory structure created:")
            self.logger.info(f"   Provider: {provider}")
            self.logger.info(f"   Model: {model}")
            self.logger.info(f"   Voice: {voice}")
            self.logger.info(f"   WAV dir: {wav_dir}")
            self.logger.info(f"   Metadata: {metadata_file}")

            return wav_dir, metadata_file

        except Exception as e:
            self.logger.error(f"❌ Lỗi tạo cấu trúc thư mục: {e}")
            raise

    def create_provider_structure_clone(self, provider: str, model: str, voice: str) -> Tuple[Path, Path]:
        """
        Create directory structure for clone operations: provider/model/voice/

        Args:
            provider: Provider name (minimax, etc.)
            model: Model name (default, neural, etc.)
            voice: Voice name (cloned_voice, etc.)

        Returns:
            Tuple containing (wav_dir, metadata_file)
        """
        try:
            # Create directory paths for clone structure
            # Structure: provider/voice/
            provider_dir = self.base_dir / provider
            model_dir = provider_dir / model
            voice_dir = model_dir / voice
            wav_dir = voice_dir / "wav"

            # Create necessary directories
            wav_dir.mkdir(parents=True, exist_ok=True)

            # Metadata file path
            metadata_file = voice_dir / "metadata.tsv"

            # Initialize metadata file with clone-specific header
            self.initialize_metadata_file_clone(metadata_file)

            self.logger.info(f"✅ Clone directory structure created:")
            self.logger.info(f"   Provider: {provider}")
            self.logger.info(f"   Model: {model}")
            self.logger.info(f"   Voice: {voice}")
            self.logger.info(f"   WAV dir: {wav_dir}")
            self.logger.info(f"   Metadata: {metadata_file}")

            return wav_dir, metadata_file

        except Exception as e:
            self.logger.error(f"❌ Lỗi tạo clone cấu trúc thư mục: {e}")
            raise

    def initialize_metadata_file(self, metadata_file: Path, columns: List[str] = None) -> bool:
        """
        Initialize metadata CSV file with header.

        Args:
            metadata_file: Path to metadata file
            columns: Custom columns list (default based on requirements)

        Returns:
            True if initialization is successful
        """
        if columns is None:
            columns = [
                "utt_id", "text_id", "text", "audio_path",  # Added text_id column
                "provider", "model", "voice", "tts_type",  # Added tts_type
                "sample_rate", "lang", "duration", "gen_date"
            ]

        try:
            if metadata_file.exists():
                self.logger.info(f"⚠️ Metadata file đã tồn tại: {metadata_file}")
                return True

            with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)

            self.logger.info(f"✅ Đã tạo metadata file: {metadata_file}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Lỗi tạo metadata file: {e}")
            return False

    def initialize_metadata_file_clone(self, metadata_file: Path) -> bool:
        """
        Initialize metadata file for clone operations with clone-specific schema.

        Args:
            metadata_file: Path to metadata file

        Returns:
            True if initialization is successful
        """
        columns = [
            "utt_id", "text_id", "text", "audio_path",
            "provider", "reference_audio", "tts_type",
            "sample_rate", "lang", "duration", "gen_date",
            "audio_url", "clone_id"
        ]

        try:
            if metadata_file.exists():
                self.logger.info(f"⚠️ Clone metadata file đã tồn tại: {metadata_file}")
                return True

            with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)

            self.logger.info(f"✅ Đã tạo clone metadata file: {metadata_file}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Lỗi tạo clone metadata file: {e}")
            return False

    def add_metadata_entry_clone(self, metadata_file: Path, text: str, audio_path: Path,
                               provider: str, reference_audio: str, tts_type: str,
                               sample_rate: int = 22050, duration: float = None, text_id: str = None,
                               audio_url: str = None, clone_id: str = None) -> bool:
        """
        Add a metadata entry for clone operations to the TSV file.

        Args:
            metadata_file: Path to metadata file
            text: Cloned text content
            audio_path: Path to audio file (relative to base_dir)
            provider: Provider name
            reference_audio: Reference audio filename
            tts_type: Operation type ("clone")
            sample_rate: Audio sample rate
            duration: Actual duration (if available)
            text_id: ID from input text file
            audio_url: Audio URL from provider
            clone_id: Clone session ID

        Returns:
            True if entry is added successfully
        """
        try:
            # Count current lines to create utt_id
            current_count = 0
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    current_count = sum(1 for _ in f) - 1  # Trừ header

            utt_id = f"{current_count + 1:03d}"

            # Estimate duration if not provided
            if duration is None:
                duration = self._estimate_duration(text)

            # Prepare data (TSV format)
            entry = [
                utt_id,
                text_id or "",  # text_id from input, empty if not provided
                text,
                str(audio_path),
                provider,
                reference_audio,
                tts_type,
                str(sample_rate),
                "vi",  # language mặc định
                f"{duration:.2f}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                audio_url or "",
                clone_id or ""
            ]

            # Write to TSV file
            with open(metadata_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='	')  # Use tab delimiter for TSV
                writer.writerow(entry)

            self.logger.debug(f"✅ Added clone metadata for: {audio_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error adding clone metadata: {e}")
            return False

    def add_metadata_entry(self, metadata_file: Path, text: str, audio_path: Path,
                          provider: str, model: str, voice: str, tts_type: str,
                          sample_rate: int = 22050, duration: float = None, text_id: str = None) -> bool:
        """
        Add a metadata entry to the TSV file.

        Args:
            metadata_file: Path to metadata file
            text: Synthesized text content
            audio_path: Path to audio file (relative to base_dir)
            provider: Provider name
            model: Model name
            voice: Voice name
            tts_type: Operation type ("synthesize")
            sample_rate: Audio sample rate
            duration: Actual duration (if available)
            text_id: ID from input text file (optional, for new format)

        Returns:
            True if entry is added successfully
        """
        try:
            # Count current lines to create utt_id
            current_count = 0
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    current_count = sum(1 for _ in f) - 1  # Trừ header

            utt_id = f"{current_count + 1:03d}"

            # Estimate duration if not provided
            if duration is None:
                duration = self._estimate_duration(text)

            # Prepare data (TSV format)
            entry = [
                utt_id,
                text_id or "",  # text_id from input, empty if not provided
                text,
                str(audio_path),
                provider,
                model,
                voice,
                tts_type,
                str(sample_rate),
                "vi",  # language mặc định
                f"{duration:.2f}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]

            # Write to TSV file
            with open(metadata_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='	')  # Use tab delimiter for TSV
                writer.writerow(entry)

            self.logger.debug(f"✅ Added metadata for: {audio_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error adding metadata: {e}")
            return False

    def _estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on text length"""
        # Adjust parameters based on real-world experience for Vietnamese
        chars_per_second = 12  # characters per second
        estimated_seconds = len(text) / chars_per_second

        # Apply reasonable limits
        return max(0.5, min(10.0, estimated_seconds))

    def get_next_utt_id(self, metadata_file: Path) -> str:
        """Get next utt_id for metadata file"""
        try:
            if not metadata_file.exists():
                return "001"

            with open(metadata_file, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f) - 1  # Trừ header

            return f"{count + 1:03d}"

        except Exception:
            return "001"

    def validate_structure(self, provider: str, model_or_reference: str, voice: str, tts_type: str = "synthesize") -> Dict[str, Any]:
        """
        Validate the integrity of the directory structure.

        Args:
            provider: Provider name
            model_or_reference: Model name (synthesize) or reference audio filename (clone)
            voice: Voice name
            tts_type: Operation type ("synthesize" or "clone")

        Returns:
            Dict containing information about the structure and detected issues
        """
        issues = {
            'missing_directories': [],
            'missing_files': [],
            'orphaned_files': [],
            'total_entries': 0,
            'is_valid': True
        }

        try:
            # Check directory structure based on operation type
            if tts_type == "clone":
                # Clone structure: provider/reference_audio/voice/
                provider_dir = self.base_dir / provider
                reference_dir = provider_dir / model_or_reference
                voice_dir = reference_dir / voice
                wav_dir = voice_dir / "wav"
                metadata_file = voice_dir / "metadata.tsv"
            else:  # synthesize
                # Synthesize structure: provider/model/voice/
                provider_dir = self.base_dir / provider
                model_dir = provider_dir / model_or_reference
                voice_dir = model_dir / voice
                wav_dir = voice_dir / "wav"
                metadata_file = voice_dir / "metadata.tsv"

            # Check missing directories
            paths_to_check = [provider_dir, voice_dir, wav_dir]
            if tts_type == "clone":
                paths_to_check.insert(1, reference_dir)  # Add reference_dir for clone
            else:
                paths_to_check.insert(1, model_dir)  # Add model_dir for synthesize

            for path in paths_to_check:
                if not path.exists():
                    issues['missing_directories'].append(str(path))
                    issues['is_valid'] = False

            # Check metadata file
            if not metadata_file.exists():
                issues['missing_files'].append(str(metadata_file))
                issues['is_valid'] = False
            else:
                # Count entries in metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    issues['total_entries'] = sum(1 for _ in f) - 1  # Trừ header

                # Check orphaned files (audio files not in metadata)
                if wav_dir.exists():
                    audio_files = {f.name for f in wav_dir.iterdir() if f.suffix.lower() == '.wav'}

                    # Read metadata to check
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        metadata_files = {row.get('audio_path', '').split('/')[-1] for row in reader}

                    orphaned = audio_files - metadata_files
                    issues['orphaned_files'] = list(orphaned)

        except Exception as e:
            self.logger.error(f"❌ Error validating structure: {e}")
            issues['is_valid'] = False

        return issues

    def get_structure_summary(self) -> Dict[str, Any]:
        """Get a summary of the directory structure for both synthesize and clone operations"""
        summary = {
            'total_providers': 0,
            'total_synthesize_models': 0,
            'total_clone_references': 0,
            'total_voices': 0,
            'total_audio_files': 0,
            'total_metadata_entries': 0,
            'providers': []
        }

        try:
            if not self.base_dir.exists():
                return summary

            # Iterate through directory structure
            for provider_dir in self.base_dir.iterdir():
                if provider_dir.is_dir():
                    summary['total_providers'] += 1
                    provider_info = {
                        'name': provider_dir.name,
                        'synthesize_models': [],
                        'clone_references': []
                    }

                    # Check for both synthesize (model dirs) and clone (reference dirs) structures
                    for subdir in provider_dir.iterdir():
                        if subdir.is_dir():
                            # Check if it's a synthesize model directory
                            model_voices = [v for v in subdir.iterdir() if v.is_dir()]
                            if model_voices:
                                # This is a synthesize structure: provider/model/voice/
                                summary['total_synthesize_models'] += 1
                                model_info = {
                                    'name': subdir.name,
                                    'type': 'synthesize',
                                    'voices': []
                                }

                                for voice_dir in model_voices:
                                    if voice_dir.is_dir():
                                        summary['total_voices'] += 1

                                        # Count audio files
                                        wav_dir = voice_dir / "wav"
                                        audio_count = 0
                                        if wav_dir.exists():
                                            audio_count = sum(1 for f in wav_dir.iterdir()
                                                            if f.suffix.lower() == '.wav')
                                            summary['total_audio_files'] += audio_count

                                        # Count metadata entries
                                        metadata_file = voice_dir / "metadata.tsv"
                                        metadata_count = 0
                                        if metadata_file.exists():
                                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                                metadata_count = sum(1 for _ in f) - 1  # Trừ header
                                                summary['total_metadata_entries'] += metadata_count

                                        model_info['voices'].append({
                                            'name': voice_dir.name,
                                            'audio_files': audio_count,
                                            'metadata_entries': metadata_count
                                        })

                                provider_info['synthesize_models'].append(model_info)

                            # Check if it's a clone reference directory
                            reference_voices = [v for v in subdir.iterdir() if v.is_dir()]
                            if reference_voices:
                                # This is a clone structure: provider/reference/voice/
                                summary['total_clone_references'] += 1
                                reference_info = {
                                    'name': subdir.name,
                                    'type': 'clone',
                                    'voices': []
                                }

                                for voice_dir in reference_voices:
                                    if voice_dir.is_dir():
                                        summary['total_voices'] += 1

                                        # Count audio files
                                        wav_dir = voice_dir / "wav"
                                        audio_count = 0
                                        if wav_dir.exists():
                                            audio_count = sum(1 for f in wav_dir.iterdir()
                                                            if f.suffix.lower() == '.wav')
                                            summary['total_audio_files'] += audio_count

                                        # Count metadata entries
                                        metadata_file = voice_dir / "metadata.tsv"
                                        metadata_count = 0
                                        if metadata_file.exists():
                                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                                metadata_count = sum(1 for _ in f) - 1  # Trừ header
                                                summary['total_metadata_entries'] += metadata_count

                                        reference_info['voices'].append({
                                            'name': voice_dir.name,
                                            'audio_files': audio_count,
                                            'metadata_entries': metadata_count
                                        })

                                provider_info['clone_references'].append(reference_info)

                    summary['providers'].append(provider_info)

        except Exception as e:
            self.logger.error(f"❌ Error getting structure summary: {e}")

        return summary

    def cleanup_orphaned_files(self, provider: str, model_or_reference: str, voice: str, tts_type: str = "synthesize", dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up orphaned files.

        Args:
            provider: Provider name
            model_or_reference: Model name (synthesize) or reference audio filename (clone)
            voice: Voice name
            tts_type: Operation type ("synthesize" or "clone")
            dry_run: If True, only display what will be removed without actually removing

        Returns:
            Dict containing information about the files to be cleaned up
        """
        result = {
            'files_to_remove': [],
            'total_size': 0,
            'removed_count': 0
        }

        try:
            # Determine directory structure based on operation type
            if tts_type == "clone":
                # Clone structure: provider/reference_audio/voice/
                wav_dir = self.base_dir / provider / model_or_reference / voice / "wav"
                metadata_file = self.base_dir / provider / model_or_reference / voice / "metadata.tsv"
            else:  # synthesize
                # Synthesize structure: provider/model/voice/
                wav_dir = self.base_dir / provider / model_or_reference / voice / "wav"
                metadata_file = self.base_dir / provider / model_or_reference / voice / "metadata.tsv"

            if not (wav_dir.exists() and metadata_file.exists()):
                return result

            # Read metadata to know which files are valid
            valid_files = set()
            with open(metadata_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    audio_path = row.get('audio_path', '')
                    if audio_path:
                        valid_files.add(Path(audio_path).name)

            # Find orphaned files
            for audio_file in wav_dir.iterdir():
                if audio_file.suffix.lower() == '.wav' and audio_file.name not in valid_files:
                    result['files_to_remove'].append(str(audio_file))
                    result['total_size'] += audio_file.stat().st_size

                    if not dry_run:
                        audio_file.unlink()
                        result['removed_count'] += 1

            self.logger.info(f"{'✅' if not dry_run else '📋'} Found {len(result['files_to_remove'])} orphaned files")

        except Exception as e:
            self.logger.error(f"❌ Error cleaning up orphaned files: {e}")

        return result
