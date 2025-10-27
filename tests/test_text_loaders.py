#!/usr/bin/env python3
# ============================================================
# Text Loaders Test
# Comprehensive test for text_loaders module using pytest
# ============================================================

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
import json
import csv

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.dataset.text_loaders import (
    TextFileLoader,
    SimpleCSVLoader,
    CustomTextLoader,
    TextLoaderFactory
)


@pytest.fixture
def test_dir():
    """Create temporary test directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_files(test_dir):
    """Create sample data files for testing"""

    # Province file
    province_file = test_dir / "provinces.txt"
    with open(province_file, 'w', encoding='utf-8') as f:
        f.write("Hồ Chí Minh\n")
        f.write("Hà Nội\n")
        f.write("# This is a comment\n")
        f.write("Đà Nẵng\n")
        f.write("\n")  # Empty line
        f.write("Cần Thơ\n")

    # District CSV file
    district_csv = test_dir / "districts.csv"
    with open(district_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['district', 'province'])
        writer.writerow(['Quận 1', 'Hồ Chí Minh'])
        writer.writerow(['Quận Bình Thạnh', 'Hồ Chí Minh'])
        writer.writerow(['Quận Ba Đình', 'Hà Nội'])

    # District text file
    district_txt = test_dir / "districts.txt"
    with open(district_txt, 'w', encoding='utf-8') as f:
        f.write("Quận Tân Bình\n")
        f.write("# Comment line\n")
        f.write("Quận Thủ Đức\n")

    # Commune CSV file
    commune_csv = test_dir / "communes.csv"
    with open(commune_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['commune', 'district', 'province'])
        writer.writerow(['Phường Bến Nghé', 'Quận 1', 'Hồ Chí Minh'])
        writer.writerow(['Phường Nguyễn Thái Bình', 'Quận 1', 'Hồ Chí Minh'])
        writer.writerow(['Phường Phúc Xá', 'Quận Ba Đình', 'Hà Nội'])

    # Custom CSV file
    custom_csv = test_dir / "custom.csv"
    with open(custom_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['text', 'language', 'category'])
        writer.writerow(['Xin chào Việt Nam', 'vi', 'greeting'])
        writer.writerow(['Hello world', 'en', 'greeting'])
        writer.writerow(['Cảm ơn bạn', 'vi', 'thanks'])

    # Custom JSON file
    custom_json = test_dir / "custom.json"
    with open(custom_json, 'w', encoding='utf-8') as f:
        json.dump([
            {"text": "Tôi yêu lập trình", "language": "vi"},
            {"text": "I love programming", "language": "en"},
            {"content": "Machine learning is amazing", "type": "tech"}
        ], f, ensure_ascii=False, indent=2)

    # Custom JSONL file
    custom_jsonl = test_dir / "custom.jsonl"
    with open(custom_jsonl, 'w', encoding='utf-8') as f:
        f.write('{"text": "Dữ liệu văn bản đầu tiên", "category": "sample"}\n')
        f.write('{"text": "Second text data", "category": "sample"}\n')
        f.write('{"transcript": "Third text with different field", "category": "sample"}\n')

    # Custom text file
    custom_txt = test_dir / "custom.txt"
    with open(custom_txt, 'w', encoding='utf-8') as f:
        f.write("Dòng văn bản đầu tiên\n")
        f.write("# Đây là comment\n")
        f.write("Dòng văn bản thứ hai\n")
        f.write("Dòng văn bản thứ ba\n")

    return test_dir


def test_text_file_loader_with_id_format(sample_files):
    """Test TextFileLoader with id\\ttext format"""
    # Create file with ID format for testing
    id_file = sample_files / "provinces_with_id.txt"
    with open(id_file, 'w', encoding='utf-8') as f:
        f.write("1\tHồ Chí Minh\n")
        f.write("2\tHà Nội\n")
        f.write("3\tĐà Nẵng\n")
        f.write("4\tCần Thơ\n")

    loader = TextFileLoader(id_file)

    # Test successful loading with ID format
    text_items = loader.load()
    expected_items = [
        ("1", "Hồ Chí Minh"),
        ("2", "Hà Nội"),
        ("3", "Đà Nẵng"),
        ("4", "Cần Thơ")
    ]

    assert len(text_items) == 4
    assert text_items == expected_items


def test_text_file_loader_without_id_format(sample_files):
    """Test TextFileLoader auto-generates IDs when no ID format"""
    loader = TextFileLoader(sample_files / "provinces.txt")

    # Test successful loading without ID format (auto-generate)
    text_items = loader.load()
    expected_items = [
        ("1", "Hồ Chí Minh"),
        ("2", "Hà Nội"),
        ("3", "# This is a comment"),
        ("4", "Đà Nẵng"),
        ("6", "Cần Thơ")  # Line number 6 (line 5 is empty and skipped)
    ]

    assert len(text_items) == 5  # 5 valid items (empty line correctly skipped)
    assert text_items == expected_items


def test_text_file_loader_with_mixed_format(sample_files):
    """Test TextFileLoader with mixed format (some with ID, some without)"""
    # Create file with mixed format
    mixed_file = sample_files / "mixed_format.txt"
    with open(mixed_file, 'w', encoding='utf-8') as f:
        f.write("1\tValid text with ID\n")
        f.write("Invalid line without tab\n")
        f.write("2\tAnother valid text\n")
        f.write("Third line without ID\n")

    loader = TextFileLoader(mixed_file)
    text_items = loader.load()

    expected_items = [
        ("1", "Valid text with ID"),
        ("2", "Invalid line without tab"),  # Should auto-generate ID as line number 2
        ("3", "Another valid text"),
        ("4", "Third line without ID")      # Should auto-generate ID as line number 4
    ]

    assert len(text_items) == 4
    assert text_items == expected_items


def test_simple_csv_loader(sample_files):
    """Test SimpleCSVLoader with required id and text columns"""
    loader = SimpleCSVLoader(sample_files / "districts.csv")
    text_items = loader.load()

    # Should load (id, text) tuples
    expected_items = [
        ("1", "Quận 1"),
        ("2", "Quận Bình Thạnh"),
        ("3", "Quận Ba Đình")
    ]

    assert len(text_items) == 3
    assert text_items == expected_items


def test_simple_csv_loader_with_column_specification(sample_files):
    """Test SimpleCSVLoader with specific column"""
    # Test with explicit column specification
    loader = SimpleCSVLoader(sample_files / "districts.csv", text_column="district")
    text_items = loader.load()

    expected_items = [
        ("1", "Quận 1"),
        ("2", "Quận Bình Thạnh"),
        ("3", "Quận Ba Đình")
    ]
    assert text_items == expected_items

    # Test with commune CSV
    loader = SimpleCSVLoader(sample_files / "communes.csv", text_column="commune")
    text_items = loader.load()

    expected_items = [
        ("1", "Phường Bến Nghé"),
        ("2", "Phường Nguyễn Thái Bình"),
        ("3", "Phường Phúc Xá")
    ]
    assert text_items == expected_items


def test_simple_csv_loader_auto_column_detection(sample_files):
    """Test SimpleCSVLoader auto-detecting text columns"""
    loader = SimpleCSVLoader(sample_files / "custom.csv")
    text_items = loader.load()

    # Should find "text" column automatically
    expected_items = [
        ("1", "Xin chào Việt Nam"),
        ("2", "Hello world"),
        ("3", "Cảm ơn bạn")
    ]
    assert text_items == expected_items


def test_custom_text_loader_csv(sample_files):
    """Test CustomTextLoader with CSV file"""
    # Test without filters
    loader = CustomTextLoader(sample_files / "custom.csv")
    texts = loader.load()

    expected_texts = ["Xin chào Việt Nam", "Hello world", "Cảm ơn bạn"]

    assert len(texts) == 3
    assert set(texts) == set(expected_texts)

    # Test with column specification
    loader = CustomTextLoader(sample_files / "custom.csv", text_column="text")
    text_items = loader.load()

    expected_items = [
        ("1", "Xin chào Việt Nam"),
        ("2", "Hello world"),
        ("3", "Cảm ơn bạn")
    ]
    assert len(text_items) == 3
    assert text_items == expected_items

    # Test with filters
    loader = CustomTextLoader(
        sample_files / "custom.csv",
        text_column="text",
        filters={"language": "vi"}
    )
    text_items = loader.load()
    expected_items = [
        ("1", "Xin chào Việt Nam"),
        ("3", "Cảm ơn bạn")
    ]

    assert len(text_items) == 2
    assert text_items == expected_items


def test_custom_text_loader_json(sample_files):
    """Test CustomTextLoader with JSON file"""
    loader = CustomTextLoader(sample_files / "custom.json")
    text_items = loader.load()

    expected_items = [
        ("1", "Tôi yêu lập trình"),
        ("2", "I love programming")
    ]

    assert len(text_items) == 2
    assert text_items == expected_items


def test_custom_text_loader_jsonl(sample_files):
    """Test CustomTextLoader with JSONL file"""
    loader = CustomTextLoader(sample_files / "custom.jsonl")
    text_items = loader.load()

    expected_items = [
        ("1", "Dữ liệu văn bản đầu tiên"),
        ("2", "Second text data"),
        ("3", "Third text with different field")
    ]

    assert len(text_items) == 3
    assert text_items == expected_items


def test_custom_text_loader_text(sample_files):
    """Test CustomTextLoader with text file"""
    loader = CustomTextLoader(sample_files / "custom.txt")
    text_items = loader.load()

    expected_items = [
        ("1", "Dòng văn bản đầu tiên"),
        ("2", "Dòng văn bản thứ hai"),
        ("3", "Dòng văn bản thứ ba")
    ]

    assert len(text_items) == 3
    assert text_items == expected_items


def test_text_loader_factory_auto_detection(sample_files):
    """Test TextLoaderFactory auto-detection"""
    # Test CSV detection
    loader = TextLoaderFactory.create_loader(sample_files / "districts.csv", "auto")
    assert isinstance(loader, SimpleCSVLoader)

    # Test text detection
    loader = TextLoaderFactory.create_loader(sample_files / "provinces.txt", "auto")
    assert isinstance(loader, TextFileLoader)

    # Test custom detection for JSON
    loader = TextLoaderFactory.create_loader(sample_files / "custom.json", "auto")
    assert isinstance(loader, CustomTextLoader)


def test_text_loader_factory_explicit_types(sample_files):
    """Test TextLoaderFactory with explicit loader types"""
    # Test explicit text loader
    loader = TextLoaderFactory.create_loader(sample_files / "provinces.txt", "text")
    assert isinstance(loader, TextFileLoader)
    text_items = loader.load()
    assert len(text_items) == 6  # 6 items with auto-generated IDs

    # Test explicit CSV loader
    loader = TextLoaderFactory.create_loader(sample_files / "districts.csv", "csv")
    assert isinstance(loader, SimpleCSVLoader)
    text_items = loader.load()
    assert len(text_items) == 3

    # Test explicit custom loader
    loader = TextLoaderFactory.create_loader(
        sample_files / "custom.csv",
        "custom",
        text_column="text"
    )
    assert isinstance(loader, CustomTextLoader)
    text_items = loader.load()
    assert len(text_items) == 3


def test_text_loader_factory_invalid_type(sample_files):
    """Test TextLoaderFactory with invalid loader type"""
    with pytest.raises(ValueError, match="Unsupported loader type"):
        TextLoaderFactory.create_loader(sample_files / "test.txt", "invalid_type")


def test_text_loader_validation(sample_files):
    """Test text loader validation"""
    # Test valid file
    loader = TextFileLoader(sample_files / "provinces.txt")
    assert loader.validate_source() is True

    # Test invalid file
    loader = TextFileLoader(sample_files / "nonexistent.txt")
    assert loader.validate_source() is False


def test_edge_cases(sample_files):
    """Test edge cases and error conditions"""
    # Test empty file - should return empty list since no lines exist
    empty_file = sample_files / "empty.txt"
    with open(empty_file, 'w', encoding='utf-8') as f:
        f.write("")

    loader = TextFileLoader(empty_file)
    text_items = loader.load()
    assert len(text_items) == 0  # Empty file has no lines

    # Test file with only comments and empty lines - loads all with auto IDs
    comment_file = sample_files / "comments.txt"
    with open(comment_file, 'w', encoding='utf-8') as f:
        f.write("# This is a comment\n")
        f.write("\n")
        f.write("# Another comment\n")
        f.write("   \n")
        f.write("Valid text line\n")

    loader = TextFileLoader(comment_file)
    text_items = loader.load()
    expected_items = [
        ("1", "# This is a comment"),
        ("2", ""),
        ("3", "# Another comment"),
        ("4", "   "),
        ("5", "Valid text line")
    ]
    assert len(text_items) == 5  # All lines including comments and empty
    assert text_items == expected_items
