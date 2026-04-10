# TTS Gateway API

A unified REST API gateway for routing Text-to-Speech (TTS) requests to multiple providers.

## Architecture

```
Client → Gateway (FastAPI) → ProviderRouter → ProviderAdapter → Provider Instance
                                                      ↑
                                              (Direct/HTTP call)
```

The Gateway uses an **abstraction layer** (`ProviderAdapter`) that allows seamless migration from direct in-process calls to HTTP microservices in the future.

## Features

- **Unified API**: Single endpoint for all TTS providers
- **Provider Routing**: Automatic routing based on `provider` field
- **Schema Validation**: Pydantic models for request/response validation
- **Health Monitoring**: Check status of all providers
- **Auto-Registration**: Automatically registers available providers on startup
- **Ready for Scale**: Abstraction layer supports both direct and HTTP calls

## Supported Providers

| Provider | Type | Notes |
|----------|------|-------|
| `cartesia` | Cloud | Cartesia Sonic TTS |
| `gemini` | Cloud | Google Gemini TTS |
| `gtts` | Local/Cloud | Google Text-to-Speech (free tier) |
| `elevenlabs` | Cloud | ElevenLabs TTS |
| `xiaomi` | Cloud | Xiaomi OmniVoice (voice cloning) |
| `vnpost` | Cloud | VNPost TTS |
| `minimax_selenium` | Cloud | MiniMax TTS (via Selenium) |

## Installation

```bash
# Install gateway dependencies
pip install -r gateway/requirements.txt

# Or install with main project
pip install -r requirements.txt
pip install fastapi uvicorn
```

## Usage

### Start the Gateway

```bash
# Development mode with auto-reload
PYTHONPATH=. python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
PYTHONPATH=. python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000

# Or using the main script
PYTHONPATH=. python gateway/main.py
```

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

#### 2. List Providers
```bash
GET /providers
```

#### 3. Get Provider Info
```bash
GET /providers/{provider_name}
```

#### 4. Synthesize (Main Endpoint)
```bash
POST /tts
```

**Request Body:**
```json
{
    "provider": "cartesia",
    "text": "Xin chào, đây là giọng nói được tạo ra.",
    "model": "sonic-3",
    "voice_config": {
        "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
        "language": "vi",
        "volume": 1.0,
        "speed": 1.0,
        "emotion": "neutral"
    },
    "audio_config": {
        "container": "mp3",
        "encoding": "pcm_f32le",
        "sample_rate": 44100
    }
}
```

**Response:**
```json
{
    "success": true,
    "text": "Xin chào, đây là giọng nói được tạo ra.",
    "audio_url": "/path/to/output_file.mp3",
    "provider": "cartesia",
    "model": "sonic-3",
    "effective_voice_config": {
        "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
        "language": "vi",
        "volume": 1.0,
        "speed": 1.0,
        "emotion": "neutral"
    },
    "effective_audio_config": {
        "container": "mp3",
        "encoding": "pcm_f32le",
        "sample_rate": 44100
    }
}
```

#### 5. Voice Cloning (Multipart Form)
```bash
POST /clone
```

For voice cloning providers (Xiaomi, MiniMax). Upload reference audio file via multipart form.

**Form Fields:**
- `provider`: Provider name (e.g., 'xiaomi')
- `text`: Text to synthesize
- `reference_audio`: Audio file to clone from (upload file)
- `reference_text`: Optional transcript of reference audio
- `language`, `enhance_speech`, `volume`, `speed`, etc.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/clone \
    -F "provider=xiaomi" \
    -F "text=Xin chào" \
    -F "reference_audio=@/path/to/reference.wav" \
    -F "language=vi"
```

#### 6. Get Audio File
```bash
GET /audio/{filename}
```

## Examples

### Using cURL

```bash
# Simple request with gTTS (no API key needed)
curl -X POST http://localhost:8000/tts \
    -H "Content-Type: application/json" \
    -d '{
        "provider": "gtts",
        "text": "Xin chào thế giới",
        "voice_config": {"voice_id": "vi", "language": "vi"}
    }'

# Full request with Cartesia
curl -X POST http://localhost:8000/tts \
    -H "Content-Type: application/json" \
    -d '{
        "provider": "cartesia",
        "model": "sonic-3",
        "text": "Chào mừng đến với TTS Gateway.",
        "voice_config": {
            "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
            "language": "vi",
            "speed": 1.0,
            "emotion": "neutral"
        },
        "audio_config": {
            "container": "mp3",
            "sample_rate": 44100
        }
    }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    json={
        "provider": "gtts",
        "text": "Xin chào thế giới",
        "voice_config": {"voice_id": "vi", "language": "vi"}
    }
)

result = response.json()
if result["success"]:
    print(f"Audio file: {result['audio_url']}")
else:
    print(f"Error: {result['error']['message']}")
```

## Configuration

### Using .env File

Copy the example environment file and update with your settings:

```bash
cp gateway/.env.example .env
# Edit .env with your API keys
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_OUTPUT_DIR` | `./gateway_output` | Directory for generated audio files |
| `TTS_UPLOAD_DIR` | `./gateway_output/uploads` | Directory for uploaded reference audio |
| `TTS_PROVIDERS_CONFIG` | `./config/providers.yaml` | Path to providers YAML config |
| `TTS_GATEWAY_HOST` | `0.0.0.0` | Gateway bind host |
| `TTS_GATEWAY_PORT` | `8000` | Gateway bind port |
| `TTS_GATEWAY_RELOAD` | `false` | Enable auto-reload (dev mode) |
| `TTS_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TTS_CORS_ORIGINS` | `*` | Comma-separated list of allowed CORS origins |

### Provider API Keys

| Variable | Provider | Description |
|----------|----------|-------------|
| `CARTESIA_API_KEYS` | cartesia | Comma-separated API keys |
| `ELEVENLABS_API_KEYS` | elevenlabs | Comma-separated API keys |
| `GEMINI_API_KEY` | gemini | Google Gemini API key |
| `GEMINI_VERTEX_PROJECT` | gemini | GCP project ID for Vertex AI |
| `GEMINI_VERTEX_LOCATION` | gemini | GCP location for Vertex AI |
| `MINIMAX_API_KEY` | minimax | MiniMax API key |
| `VNPOST_API_KEY` | vnpost | VNPost API key |
| `XIAOMI_STT_API_BASE` | xiaomi | STT API base URL |
| `XIAOMI_STT_ENDPOINT` | xiaomi | STT API endpoint |

### Provider Configuration

Create a YAML config file at `./config/providers.yaml`:

```yaml
providers:
  cartesia:
    provider_config:
      name: cartesia
      models: ["sonic-3"]
      default_model: "sonic-3"
      credentials:
        envs: ["CARTESIA_API_KEY"]
        api_keys: ["your-api-key-here"]
  
  gemini:
    provider_config:
      name: gemini
      models: ["gemini-2.5-flash-preview-tts"]
      default_model: "gemini-2.5-flash-preview-tts"
      credentials:
        envs: ["GEMINI_API_KEY"]
        api_keys: ["your-api-key-here"]
```

## Testing

Run the test suite:

```bash
# Start gateway first (in another terminal)
PYTHONPATH=. python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000

# Run tests
PYTHONPATH=. python gateway/test_gateway.py
```

## Scaling to Microservices

The Gateway uses an abstraction layer (`ProviderAdapter`) that makes it easy to migrate to microservices:

**Current (Direct):**
```
Gateway → DirectProviderAdapter → Provider.synthesize()
```

**Future (HTTP):**
```
Gateway → HTTPProviderAdapter → Provider Service API
```

To add HTTP support in the future:

1. Create `HTTPProviderAdapter` class implementing the same interface
2. Update `ProviderRouter` to use HTTP adapters based on configuration
3. Each provider becomes an independent FastAPI service

No changes needed to the client API!

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
gateway/
├── __init__.py          # Package exports
├── main.py              # FastAPI application
├── schemas.py           # Request/response Pydantic models
├── router.py            # Provider routing logic
├── test_gateway.py      # Test suite
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Error Handling

The Gateway provides detailed error information:

```json
{
    "success": false,
    "text": "Hello",
    "audio_url": null,
    "provider": "cartesia",
    "error": {
        "message": "Synthesis failed",
        "detail": "API rate limit exceeded"
    }
}
```

HTTP status codes:
- `200`: Request processed (check `success` field for result)
- `400`: Invalid request (validation error)
- `404`: Provider not found
- `503`: Gateway not initialized
- `500`: Internal server error
