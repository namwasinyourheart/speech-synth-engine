# MiniMax Selenium Provider Examples

This directory contains comprehensive examples and documentation for using the MiniMax Selenium Provider.

## Files

### 📚 Documentation
- `docs/minimax_selenium_provider_usage.md` - Complete API documentation and usage guide

### 📓 Notebooks
- `notebooks/minimax_examples.ipynb` - Interactive Jupyter notebook with detailed examples
- `notebooks/try_sse.ipynb` - General speech synthesis examples (reference)

### 🚀 Quick Start
- `examples/minimax_quickstart.py` - Simple script to get started quickly

### 🧪 Tests
- `tests/test_minimax_selenium_provider.py` - Comprehensive test suite

## Quick Start

1. **Set up credentials:**
```bash
export MINIMAX_GOOGLE_EMAIL="your_email@gmail.com"
export MINIMAX_GOOGLE_PASSWORD="your_password"
```

2. **Run quick start:**
```bash
cd /home/nampv1/projects/tts/speech-synth-engine
python examples/minimax_quickstart.py
```

3. **Use in Jupyter:**
```bash
cd notebooks
jupyter notebook minimax_examples.ipynb
```

## Usage Patterns

### Basic Voice Cloning
```python
from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider
from pathlib import Path

# Setup
config = {
    "google_email": "your_email@gmail.com",
    "google_password": "your_password",
    "headless": False
}

provider = MiniMaxSeleniumProvider("minimax", config)

# Clone voice
reference_audio = Path("reference_voice.wav")
text = "Hello, this is voice cloning"
output = Path("output.wav")

success = provider.clone(text, reference_audio, output)
```

### Batch Processing
```python
from speech_synth_engine.dataset.text_loaders import TextFileLoader

# Load texts
text_file = Path("texts.txt")
loader = TextFileLoader(text_file)
texts = loader.load()

# Batch clone
batch_result = provider.clone_batch(text_file, reference_audio, output_dir)
print(f"Success rate: {batch_result['success_rate']:.1f}%")
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `google_email` | Required | Google account email |
| `google_password` | Required | Google account password |
| `headless` | `false` | Run browser in headless mode |
| `language` | `"Vietnamese"` | Target language |
| `max_wait_time` | `300` | Maximum wait time in seconds |
| `batch_processing` | `true` | Enable batch processing |
| `max_batch_size` | `10` | Maximum batch size |

## Text File Formats

### Simple Text (auto IDs)
```
Hello world
This is a test
Multiple lines
```

### Tab Separated (custom IDs)
```
001	Hello from tab format
002	Second line with tab
003	Third line
```

### CSV Format
```csv
id,text
101,CSV first line
102,CSV second line
```

## Requirements

- Python 3.8+
- Selenium WebDriver
- Chrome browser
- Valid Google account with MiniMax access
- Reference audio files (WAV/MP3)

## Troubleshooting

1. **Authentication Issues**: Verify Google account credentials
2. **Upload Problems**: Check reference audio format and size
3. **Timeout Errors**: Increase timeout values in configuration
4. **Browser Issues**: Ensure Chrome is installed and up-to-date

## Support

For issues and questions, check:
1. Test suite for usage patterns
2. Example notebook for detailed examples
3. Documentation for API reference
4. Provider logs for error details
