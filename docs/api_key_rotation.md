# API Key Rotation for ElevenLabs Provider

This document explains how to use the API key rotation feature in the ElevenLabs TTS provider.

## Setup

### Environment Variables

You can provide multiple API keys using environment variables. The provider will automatically rotate through them when a key's quota is exceeded.

```bash
# Single API key (legacy)
ELEVENLABS_API_KEY=your_api_key_here

# Multiple API keys
ELEVENLABS_API_KEY_1=your_first_api_key
ELEVENLABS_API_KEY_2=your_second_api_key
ELEVENLABS_API_KEY_3=your_third_api_key
```

### Configuration

Alternatively, you can provide API keys in the configuration when initializing the provider:

```python
config = {
    'api_keys': [
        'your_first_api_key',
        'your_second_api_key',
        'your_third_api_key'
    ],
    'model_id': 'eleven_multilingual_v2',
    'default_voice_id': 'pNInz6obpgDQGcFmaJgB'
}

provider = ElevenLabsProvider('elevenlabs', config=config)
```

## How It Works

1. The provider will start with the first API key.
2. When a "quota exceeded" error is detected, the current key is marked as exhausted.
3. The provider automatically switches to the next available key.
4. If all keys are exhausted, an error will be logged.

## Logging

The provider logs key rotation events and quota issues:

- When a key is marked as exhausted (quota exceeded)
- When rotating to a new key
- When no more keys are available

## Error Handling

The provider handles the following scenarios:
- Quota exceeded errors (automatic key rotation)
- Invalid API keys (skipped)
- Network errors (retried with the same key)

## Best Practices

1. **Use multiple API keys** to ensure high availability.
2. **Monitor your logs** to track key usage and rotation.
3. **Rotate keys regularly** to distribute load.
4. **Set up alerts** for when keys are running low.

## Example

```python
from speech_synth_engine.providers.elevenlabs_provider import ElevenLabsProvider
from pathlib import Path

# Initialize with multiple API keys
provider = ElevenLabsProvider('elevenlabs')

# The provider will automatically handle key rotation
result = provider.synthesize(
    "Hello, this is a test of the API key rotation feature.",
    output_file=Path("output.wav")
)

if result:
    print("Synthesis successful!")
else:
    print("Synthesis failed.")
```
