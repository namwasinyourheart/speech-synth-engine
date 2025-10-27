# ============================================================
# MiniMax Selenium Provider Documentation
# TTS Provider using MiniMax voice cloning via Selenium automation
# ============================================================

## Overview

The `MiniMaxSeleniumProvider` is a TTS provider that uses Selenium automation to interact with MiniMax's voice cloning service. It supports both direct text-to-speech synthesis and voice cloning from reference audio.

## Features

- **Voice Cloning**: Upload reference audio and generate speech in the cloned voice
- **Google OAuth Integration**: Automated authentication with Google accounts
- **Vietnamese Language Support**: Optimized for Vietnamese text and voices
- **Robust Error Handling**: Comprehensive error handling and logging
- **Screenshot Debugging**: Automatic screenshots on failures for debugging

## Installation

1. Install required dependencies:
```bash
pip install -r requirements_selenium.txt
```

2. Install Chrome browser if not already installed

3. Set up environment variables:
```bash
export MINIMAX_GOOGLE_EMAIL="your_google_email@gmail.com"
export MINIMAX_GOOGLE_PASSWORD="your_google_password"
```

## Configuration

Add to your `config/providers.yaml`:

```yaml
# MiniMax Provider - voice cloning via Selenium automation
minimax_selenium:
  class: "speech_synth_engine.providers.minimax_selenium_provider.MiniMaxSeleniumProvider"
  base_url: "https://www.minimax.io/audio/voices-cloning"
  google_email: "${MINIMAX_GOOGLE_EMAIL}"
  google_password: "${MINIMAX_GOOGLE_PASSWORD}"
  headless: false
  sample_rate: 22050
  language: "Vietnamese"
  timeout: 30
  download_timeout: 120
  max_wait_time: 300
  chars_per_second: 12
  min_duration: 0.5
  max_duration: 15.0
```

## Usage

### Basic Usage

```python
from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider
from pathlib import Path

# Initialize provider
config = {
    "google_email": "your_email@gmail.com",
    "google_password": "your_password",
    "headless": False
}

provider = MiniMaxSeleniumProvider("minimax_selenium", config)

# Synthesize text to speech
text = "Xin chào, đây là MiniMax voice cloning"
output_file = Path("output/minimax_test.wav")

success = provider.synthesize(text, "cloned_voice", output_file)
```

### Voice Cloning

```python
# Clone voice from reference audio
reference_audio = Path("path/to/reference/audio.wav")
text = "Text to synthesize with cloned voice"

success = provider.clone(text, reference_audio, output_file)
```

### With Metadata

```python
# Get comprehensive synthesis metadata
result = provider.synthesize_with_metadata(text, "cloned_voice", output_file)

print(f"Success: {result['success']}")
print(f"Error: {result['error']}")
print(f"Audio URL: {result['audio_url']}")
print(f"File info: {result['file_info']}")
```

## Authentication

The provider uses Google OAuth for authentication:

1. **First Time**: Manual login required to establish session
2. **Subsequent**: Automatic authentication using stored credentials
3. **Session Management**: Automatic session cleanup and renewal

### Security Notes

- Credentials are stored as environment variables
- Use dedicated Google account for automation
- Enable 2FA with app passwords if needed
- Consider using headless mode for production

## Supported Voices

- `cloned_voice`: Use voice cloning from uploaded reference audio
- `reference_voice`: Alternative name for cloned voice

## Error Handling

Common errors and solutions:

1. **Authentication Failed**
   - Check Google account credentials
   - Verify account is not locked
   - Check 2FA settings

2. **Element Not Found**
   - MiniMax website structure may have changed
   - Check if site is accessible
   - Update selectors if needed

3. **Timeout Errors**
   - Increase timeout values in config
   - Check internet connection
   - Verify site is responding

4. **Chrome Driver Issues**
   - Update Chrome browser
   - Reinstall undetected_chromedriver
   - Check Chrome version compatibility

## Debugging

### Screenshots
The provider automatically takes screenshots on errors:
- `minimax_auth_error.png`: Authentication failures
- `minimax_generation_error.png`: Voice generation failures
- `minimax_synthesis_error.png`: General synthesis errors

### Logging
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Headless Mode
For production or CI/CD:
```yaml
headless: true
```

## Testing

Run the test suite:
```bash
python tests/test_minimax_selenium_provider.py
```

Test categories:
- **Initialization**: Provider setup and configuration
- **Metadata**: Text validation and duration estimation
- **Dry Run**: Synthesis without actual Selenium execution
- **Real Test**: Full Selenium automation (requires credentials)

## Performance Considerations

- **Initial Load**: ~30-60 seconds for first authentication
- **Voice Generation**: 2-5 minutes depending on text length
- **Memory Usage**: ~100-200MB per Chrome instance
- **Network**: Stable internet connection required

## Limitations

- **Rate Limits**: MiniMax may have usage quotas
- **Website Changes**: Selectors may break if MiniMax updates their UI
- **Audio Quality**: Dependent on reference audio quality
- **Language Support**: Currently optimized for Vietnamese

## Troubleshooting

### Common Issues

1. **Chrome Driver Not Found**
   ```bash
   # Install Chrome driver
   sudo apt-get install chromium-chromedriver
   ```

2. **Permission Denied**
   ```bash
   # Fix Chrome permissions
   sudo chmod +x /usr/bin/google-chrome
   ```

3. **Anti-Bot Detection**
   - Use residential IP addresses
   - Add random delays between actions
   - Consider using proxy rotation

### Monitoring

Check provider health:
```python
metadata = provider.get_metadata_info()
print(f"Provider: {metadata['name']}")
print(f"Supported voices: {metadata['supported_voices']}")
print(f"Sample rate: {metadata['sample_rate']}")
```

## Contributing

When adding new Selenium providers:

1. Extend `SeleniumProvider` base class
2. Implement `authenticate()` and `generate_voice()` methods
3. Add provider-specific configuration
4. Create comprehensive tests
5. Update documentation

## License

This provider is part of the speech-synth-engine project. See main project license for details.
