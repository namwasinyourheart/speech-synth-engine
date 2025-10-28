#!/usr/bin/env python3
# ============================================================
# Text Loaders
# Hệ thống load text từ nhiều nguồn khác nhau
# ============================================================

import csv
import json
from pathlib import Path
from typing import List, Tuple, Optional, Union, Any, Dict
from abc import ABC, abstractmethod
import logging

class TextLoader(ABC):
    """Abstract base class for text loaders"""

    def __init__(self):
        self.logger = logging.getLogger(f"TextLoader.{self.__class__.__name__}")

    @abstractmethod
    def load(self, source_path: Union[str, Path]) -> List[Tuple[str, str]]:
        """
        Load text with IDs from source
        
        Args:
            source_path: Path to the source file or directory
            
        Returns:
            List of tuples containing (id, text) pairs
        """
        pass

    def validate_source(self, source_path: Union[str, Path]) -> bool:
        """
        Validate source data
        
        Args:
            source_path: Path to the source file or directory to validate
            
        Returns:
            bool: True if source is valid, False otherwise
        """
        return Path(source_path).exists()

class TextFileLoader(TextLoader):
    """Generic loader for text files - loads all lines including comments"""

    def __init__(self, encoding: str = "utf-8"):
        super().__init__()
        self.encoding = encoding

    def load(self, source_path: Union[str, Path]) -> List[Tuple[str, str]]:
        """
        Load text lines with IDs from file
        
        Args:
            source_path: Path to the text file to load
            
        Returns:
            List of tuples containing (id, text) pairs
            
        Raises:
            FileNotFoundError: If the source file doesn't exist
        """
        source_path = Path(source_path)
        if not self.validate_source(source_path):
            raise FileNotFoundError(f"File not found: {source_path}")

        text_items = []
        try:
            with open(source_path, 'r', encoding=self.encoding) as f:
                for line_num, line in enumerate(f, 1):
                    text = line.rstrip('\n\r')  # Remove only line endings, keep spaces

                    # Skip empty lines
                    if not text.strip():
                        continue

                    # Check if line has format: id\ttext
                    if '\t' in text:
                        parts = text.split('\t', 1)
                        if len(parts) == 2:
                            text_id, text_content = parts
                            text_items.append((text_id.strip(), text_content.strip()))
                        else:
                            # Malformed line, treat as text without ID
                            self.logger.warning(f"⚠️ Malformed line {line_num}, treating as text without ID")
                            text_items.append((str(line_num), text.strip()))
                    else:
                        # No tab found, auto-generate ID starting from 1
                        text_items.append((str(line_num), text.strip()))

            self.logger.info(f"✅ Loaded {len(text_items)} text items from {source_path}")
            return text_items

        except Exception as e:
            self.logger.error(f"❌ Error reading text file: {e}")
            raise


class SimpleCSVLoader(TextLoader):
    """Generic CSV loader for text data"""

    def __init__(self, source_path: Path, text_column: str = None, encoding: str = "utf-8"):
        super().__init__(source_path)
        self.text_column = text_column
        self.encoding = encoding

    def load(self) -> List[Tuple[str, str]]:
        """Load text with IDs from CSV file"""
        if not self.validate_source():
            raise FileNotFoundError(f"File not found: {self.source_path}")

        text_items = []
        try:
            with open(self.source_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)

                # Validate required columns
                if 'id' not in reader.fieldnames or 'text' not in reader.fieldnames:
                    raise ValueError(f"CSV file must have 'id' and 'text' columns. Found: {reader.fieldnames}")

                for row_num, row in enumerate(reader, 1):
                    text_id = row.get('id', '').strip()
                    text_content = row.get('text', '').strip()

                    if text_id and text_content:
                        text_items.append((text_id, text_content))

            self.logger.info(f"✅ Loaded {len(text_items)} text items from CSV {self.source_path}")
            return text_items

        except Exception as e:
            self.logger.error(f"❌ Error reading CSV file: {e}")
            raise

class CustomTextLoader(TextLoader):
    """Loader for custom text from file"""

    def __init__(self, source_path: Path, text_column: str = None, filters: Dict[str, Any] = None):
        super().__init__(source_path)
        self.text_column = text_column
        self.filters = filters or {}

    def load(self) -> List[Tuple[str, str]]:
        """Load text from custom file (CSV, JSON, or text)"""
        if not self.validate_source():
            raise FileNotFoundError(f"File not found: {self.source_path}")

        suffix = self.source_path.suffix.lower()

        if suffix == '.csv':
            return self._load_from_csv()
        elif suffix == '.json':
            return self._load_from_json()
        elif suffix == '.jsonl':
            return self._load_from_jsonl()
        else:
            # Default to text file format
            return self._load_from_text()

    def _load_from_csv(self) -> List[Tuple[str, str]]:
        """Load from CSV with id and text columns"""
        text_items = []
        try:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate required columns
                if 'id' not in reader.fieldnames or 'text' not in reader.fieldnames:
                    raise ValueError(f"CSV file must have 'id' and 'text' columns. Found: {reader.fieldnames}")

                for row_num, row in enumerate(reader, 1):
                    text_id = row.get('id', '').strip()
                    text_content = row.get('text', '').strip()

                    if text_id and text_content:
                        text_items.append((text_id, text_content))

        except Exception as e:
            self.logger.error(f"❌ Error reading CSV: {e}")
            raise

        return text_items

    def _load_from_json(self) -> List[Tuple[str, str]]:
        """Load from JSON file"""
        text_items = []
        try:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                for item_num, item in enumerate(data, 1):
                    if isinstance(item, dict):
                        text_id = item.get('id', str(item_num))
                        text_content = item.get('text', item.get('content', item.get('transcript', '')))

                        if text_content:
                            text_items.append((str(text_id), text_content))

        except Exception as e:
            self.logger.error(f"❌ Error reading JSON: {e}")
            raise

        return text_items

    def _load_from_jsonl(self) -> List[Tuple[str, str]]:
        """Load from JSONL file"""
        text_items = []
        try:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        item = json.loads(line)
                        if isinstance(item, dict):
                            text_id = item.get('id', str(line_num))
                            text_content = item.get('text', item.get('content', item.get('transcript', '')))

                            if text_content:
                                text_items.append((str(text_id), text_content))

                    except json.JSONDecodeError as e:
                        self.logger.warning(f"⚠️ Skipping malformed JSON line {line_num}: {e}")

        except Exception as e:
            self.logger.error(f"❌ Error reading JSONL: {e}")
            raise

        return text_items

    def _load_from_text(self) -> List[Tuple[str, str]]:
        """Load from text file with auto-generated IDs"""
        text_items = []
        try:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    text = line.rstrip('\n\r').strip()
                    if text:
                        text_items.append((str(line_num), text))

        except Exception as e:
            self.logger.error(f"❌ Error reading text: {e}")
            raise

        return text_items

    def _apply_filters(self, item: Dict[str, Any]) -> bool:
        """Apply filters to item"""
        if not self.filters:
            return True

        for key, expected_value in self.filters.items():
            if key not in item or item[key] != expected_value:
                return False

        return True

    def _extract_text_from_item(self, item: Dict[str, Any]) -> str:
        """Extract text from item"""
        if isinstance(item, str):
            return item

        if isinstance(item, dict):
            # Find text at common positions
            for key in ['text', 'content', 'transcript', 'sentence']:
                if key in item and isinstance(item[key], str):
                    return item[key].strip()

            # If not found, get the first string value
            for value in item.values():
                if isinstance(value, str):
                    return value.strip()

        return ""

class TextLoaderFactory:
    """Factory to create appropriate text loaders"""

    @staticmethod
    def create_loader(source_path: Path, loader_type: str = "auto", **kwargs) -> TextLoader:
        """
        Create loader based on file type and parameters

        Args:
            source_path: Path to the source file
            loader_type: Loader type ("text", "csv", "custom", "auto")
            **kwargs: Additional parameters for the loader

        Returns:
            TextLoader instance
        """
        if loader_type == "auto":
            loader_type = TextLoaderFactory._detect_loader_type(source_path)

        if loader_type == "text":
            return TextFileLoader(source_path, **kwargs)
        elif loader_type == "csv":
            return SimpleCSVLoader(source_path, **kwargs)
        elif loader_type == "custom":
            return CustomTextLoader(source_path, **kwargs)
        else:
            raise ValueError(f"Unsupported loader type: {loader_type}")

    @staticmethod
    def _detect_loader_type(source_path: Path) -> str:
        """Auto detect loader type based on file extension"""
        suffix = source_path.suffix.lower()

        if suffix == '.csv':
            return "csv"
        elif suffix in ['.txt', '.text']:
            return "text"
        elif suffix in ['.json', '.jsonl']:
            return "custom"
        else:
            # Default to text for unknown extensions
            return "text"
