# MiniMax Selenium Provider Documentation

## Overview

The **MiniMax Selenium Provider** is a comprehensive text-to-speech provider that uses **voice cloning** technology via the MiniMax web interface. It automates the entire process including Google OAuth authentication, reference audio upload, and voice generation.

## Features

- ✅ **Voice Cloning**: Clone voices from reference audio files
- ✅ **Vietnamese Support**: Optimized for Vietnamese language
- ✅ **Batch Processing**: Process multiple texts from files
- ✅ **Google OAuth**: Automated authentication
- ✅ **Error Handling**: Comprehensive error recovery
- ✅ **TextFileLoader Integration**: Support for multiple text formats

## Installation

```bash
# The provider is included in the speech-synth-engine package
cd /home/nampv1/projects/tts/speech-synth-engine
pip install -r requirements_selenium.txt
```

## Configuration

### Basic Configuration

```python
from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

config = {
    "base_url": "https://www.minimax.io/audio/voices-cloning",
    "google_email": "your_email@gmail.com",      # Required
    "google_password": "your_password",           # Required
    "headless": False,                            # Set to True for headless mode
    "sample_rate": 22050,
    "language": "Vietnamese",
    "timeout": 60,
    "download_timeout": 180,
    "max_wait_time": 300
}

provider = MiniMaxSeleniumProvider("minimax_selenium", config)
```

### Advanced Configuration

```python
advanced_config = {
    "base_url": "https://www.minimax.io/audio/voices-cloning",
    "google_email": os.getenv("MINIMAX_GOOGLE_EMAIL"),
    "google_password": os.getenv("MINIMAX_GOOGLE_PASSWORD"),
    "headless": False,
    "sample_rate": 22050,
    "language": "Vietnamese",
    "timeout": 120,
    "download_timeout": 300,
    "max_wait_time": 600,
    "batch_processing": True,
    "max_batch_size": 5,
    "batch_delay": 5,
    "chars_per_second": 15,
    "min_duration": 1.0,
    "max_duration": 30.0
}
```

## Usage Examples

### 1. Voice Cloning with Metadata

```python
# Voice cloning with comprehensive metadata (recommended approach)
result = provider.clone_with_metadata(text, reference_audio, output_file)

print(f"Success: {result['success']}")
print(f"Audio URL: {result['audio_url']}")
print(f"Estimated duration: {result['estimated_duration']:.2f}s")
print(f"File info: {result['file_info']}")
```

### 2. Basic Voice Cloning

```python
# Simple voice cloning (boolean result)
success = provider.clone(text, reference_audio, output_file)

if success:
    print("✅ Voice cloning successful")
else:
    print("❌ Voice cloning failed")
```

### 3. Batch Voice Cloning

```python
# Batch processing with TextFileLoader
batch_result = provider.clone_batch(text_file, reference_audio, output_dir)

print(f"Total: {batch_result['total_texts']}")
print(f"Processed: {batch_result['processed']}")
print(f"Success rate: {batch_result['success_rate']:.1f}%")

# Individual results
for result in batch_result['results']:
    print(f"  {result['id']}: {'✅' if result['success'] else '❌'}")
```

### 4. Synthesis with Metadata (uses clone logic)

```python
# This method now uses voice cloning logic for MiniMax
result = provider.synthesize_with_metadata(text, "cloned_voice", output_file)

if result['success']:
    print(f"✅ Success: {result['output_file']}")
else:
    print(f"❌ Failed: {result['error']}")
```

### 5. Batch Processing

```python
from speech_synth_engine.dataset.text_loaders import TextFileLoader

# Load texts from file
text_file = Path("path/to/texts.txt")
loader = TextFileLoader(text_file)
texts = loader.load()  # Returns [(id, text), ...]

print(f"Loaded {len(texts)} texts")

# Batch voice cloning
reference_audio = Path("path/to/reference_voice.wav")
output_dir = Path("output/batch")

batch_result = provider.clone_batch(text_file, reference_audio, output_dir)

print(f"Total: {batch_result['total_texts']}")
print(f"Processed: {batch_result['processed']}")
print(f"Success rate: {batch_result['success_rate']:.1f}%")
```

### 4. TextFileLoader Formats

The provider supports multiple text formats via TextFileLoader:

#### Simple Text Format
```
Hello world
This is a test
Multiple lines of text
```

#### Tab-Separated Format
```
001	Hello from tab format
002	Second line with tab
003	Third line
```

#### CSV Format
```csv
id,text
101,CSV first line
102,CSV second line
103,CSV third line
```

## API Reference

### Class: MiniMaxSeleniumProvider

#### Methods

##### `clone_with_metadata(text: str, reference_audio: Path, output_file: Path) -> Dict[str, Any]`
Clone voice with comprehensive metadata information. **Recommended method.**

**Parameters:**
- `text` (str): Text to synthesize
- `reference_audio` (Path): Path to reference audio file
- `output_file` (Path): Output audio file path

**Returns:** `Dict` with detailed results and metadata

##### `clone(text: str, reference_audio: Path, output_file: Path) -> bool`
Basic voice cloning method.

**Parameters:**
- `text` (str): Text to synthesize
- `reference_audio` (Path): Path to reference audio file
- `output_file` (Path): Output audio file path

**Returns:** `bool` - True if successful

##### `clone_batch(text_file: Path, reference_audio: Path, output_dir: Path) -> Dict[str, Any]`
Batch voice cloning from text file.

**Parameters:**
- `text_file` (Path): Path to text file (supports multiple formats)
- `reference_audio` (Path): Path to reference audio file
- `output_dir` (Path): Output directory for generated audio

**Returns:** `Dict` with batch results summary

##### `synthesize_with_metadata(text: str, voice: str, output_file: Path) -> Dict[str, Any]`
Synthesize with metadata (uses voice cloning logic for MiniMax).

**Parameters:**
- `text` (str): Text to synthesize
- `voice` (str): Voice name (typically "cloned_voice")
- `output_file` (Path): Output audio file path

**Returns:** `Dict` with detailed results

#### Properties

- `provider_info`: Dictionary with provider capabilities
- `supported_voices`: List of supported voice names
- `sample_rate`: Audio sample rate
- `language`: Language setting

## Environment Variables

Set these environment variables for easier configuration:

```bash
export MINIMAX_GOOGLE_EMAIL="your_email@gmail.com"
export MINIMAX_GOOGLE_PASSWORD="your_password"
```

## Error Handling

The provider includes comprehensive error handling:

```python
try:
    success = provider.clone(text, reference_audio, output_file)
    if success:
        print("✅ Success")
    else:
        print("❌ Failed")
except Exception as e:
    print(f"❌ Error: {e}")
    provider.cleanup()  # Always cleanup
finally:
    provider.cleanup()  # Ensure cleanup
```

## Best Practices

### 1. Reference Audio
- Use high-quality audio (WAV or MP3 format)
- Duration: 5-30 seconds recommended
- Clear speech, minimal background noise
- Same speaker throughout the audio

### 2. Text Content
- Keep text length reasonable (under 1000 characters)
- Use proper Vietnamese text with diacritics
- Avoid special characters that might cause issues

### 3. Batch Processing
- Use smaller batches (5-10 texts) for stability
- Include delays between requests
- Monitor success rates and handle failures

### 4. Authentication
- Ensure Google account has access to MiniMax
- Check account credentials regularly
- Handle authentication failures gracefully

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
```python
# Check credentials
provider = MiniMaxSeleniumProvider("test", config)
if not provider.authenticate():
    print("❌ Authentication failed")
    provider.cleanup()
```

#### 2. Upload Issues
```python
# Check reference audio
if not reference_audio.exists():
    print("❌ Reference audio not found")
elif reference_audio.stat().st_size == 0:
    print("❌ Reference audio is empty")
```

#### 3. Timeout Issues
```python
# Increase timeouts
config["max_wait_time"] = 600  # 10 minutes
config["download_timeout"] = 300  # 5 minutes
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Provider will log detailed information
provider = MiniMaxSeleniumProvider("debug_provider", config)
```

## Examples Directory

See complete examples in:
- `notebooks/minimax_examples.ipynb` - Interactive notebook with examples
- `tests/test_minimax_selenium_provider.py` - Test suite with usage examples
- `examples/` - Sample scripts and configurations

## Support

For issues and questions:
1. Check the test suite for usage patterns
2. Review the example notebook
3. Check provider logs for detailed error information
4. Ensure all dependencies are installed correctly

## License

This provider is part of the speech-synth-engine project.
