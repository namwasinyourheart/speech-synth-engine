# TTS Gateway API - Hướng dẫn sử dụng

## 1. Khởi động Gateway

```bash
# 1. Activate environment
conda activate asr

# 2. Chuyển vào thư mục project
cd /home/nampv1/projects/tts/speech-synth-engine

# 3. Start Gateway (development mode)
PYTHONPATH=. python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload

# Hoặc production mode
PYTHONPATH=. python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000
```

Gateway sẽ chạy tại: `http://localhost:8000`

---

## 2. API Endpoints

### 2.1 Root - Thông tin API

**Endpoint:** `GET /`

**Mô tả:** Lấy thông tin cơ bản về API

**Curl:**
```bash
curl http://localhost:8000/
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/")
print(response.json())
```

**Response:**
```json
{
  "name": "TTS Gateway API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "providers": "/providers",
  "synthesize": "POST /tts"
}
```

---

### 2.2 Health Check - Kiểm tra sức khỏe

**Endpoint:** `GET /health`

**Mô tả:** Kiểm tra trạng thái Gateway và các providers

**Curl:**
```bash
curl http://localhost:8000/health
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/health")
data = response.json()

print(f"Status: {data['status']}")
print(f"Providers: {data['providers']['healthy']}/{data['providers']['total']} healthy")
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-09T10:30:00.123456",
  "providers": {
    "total": 4,
    "healthy": 3,
    "details": {
      "gtts": {"provider": "gtts", "status": "healthy", "message": "..."},
      "cartesia": {"provider": "cartesia", "status": "healthy", "message": "..."},
      "gemini": {"provider": "gemini", "status": "unhealthy", "message": "API key missing"}
    }
  }
}
```

---

### 2.3 List Providers - Liệt kê providers

**Endpoint:** `GET /providers`

**Mô tả:** Lấy danh sách tất cả providers đã đăng ký và thông tin chi tiết

**Curl:**
```bash
curl http://localhost:8000/providers | python -m json.tool
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/providers")
data = response.json()

print("Registered providers:", data["registered"])
print("\nAvailable types:", data["available_types"])

# Chi tiết từng provider
for name, info in data["providers_info"].items():
    print(f"\n{name}:")
    print(f"  Voices: {info.get('supported_voices', [])}")
```

**Response:**
```json
{
  "registered": ["cartesia", "gemini", "gtts", "elevenlabs"],
  "available_types": ["cartesia", "gemini", "gtts", "elevenlabs", "xiaomi", "vnpost", "minimax_selenium"],
  "providers_info": {
    "cartesia": {
      "name": "cartesia",
      "supported_voices": ["vi"],
      "sample_rate": 44100,
      "language": "vi",
      "config": {...}
    },
    "gtts": {...}
  }
}
```

---

### 2.4 Provider Info - Chi tiết một provider

**Endpoint:** `GET /providers/{provider_name}`

**Mô tả:** Lấy thông tin chi tiết về một provider cụ thể

**Parameters:**
- `provider_name`: Tên provider (e.g., `cartesia`, `gtts`, `gemini`)

**Curl:**
```bash
# Cartesia
curl http://localhost:8000/providers/cartesia | python -m json.tool

# gTTS
curl http://localhost:8000/providers/gtts | python -m json.tool

# Gemini
curl http://localhost:8000/providers/gemini | python -m json.tool
```

**Python:**
```python
import requests

# Lấy info Cartesia
response = requests.get("http://localhost:8000/providers/cartesia")
print(response.json())

# Lấy info gTTS
response = requests.get("http://localhost:8000/providers/gtts")
print(response.json())
```

**Response (Cartesia):**
```json
{
  "cartesia": {
    "name": "cartesia",
    "supported_voices": ["vi"],
    "sample_rate": 44100,
    "language": "vi",
    "config": {...},
    "models": ["sonic-3"],
    "default_model": "sonic-3"
  }
}
```

---

### 2.5 TTS Synthesis - Tổng hợp giọng nói (CHÍNH)

**Endpoint:** `POST /tts`

**Mô tả:** Endpoint chính để tổng hợp text thành giọng nói

**Request Body Schema:**
```json
{
  "provider": "string (required)",
  "text": "string (required)",
  "model": "string (optional)",
  "voice_config": {
    "voice_id": "string",
    "volume": 0.0-1.0,
    "speed": 0.5-2.0,
    "emotion": "string",
    "language": "string",
    "pitch": "number"
  },
  "audio_config": {
    "container": "raw|wav|mp3",
    "encoding": "pcm_f32le|pcm_s16le|pcm_mulaw|pcm_alaw|mp3",
    "sample_rate": 8000|16000|22050|24000|32000|44100,
    "bit_rate": "64kbps|128kbps|192kbps|256kbps|320kbps",
    "channel": 1|2
  }
}
```

---

#### Ví dụ 1: gTTS (Đơn giản, không cần API key)

**Curl:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gtts",
    "text": "Xin chào, đây là giọng nói tiếng Việt.",
    "voice_config": {
      "voice_id": "vi",
      "language": "vi"
    },
    "audio_config": {
      "container": "wav",
      "sample_rate": 22050
    }
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    json={
        "provider": "gtts",
        "text": "Xin chào, đây là giọng nói tiếng Việt.",
        "voice_config": {
            "voice_id": "vi",
            "language": "vi"
        },
        "audio_config": {
            "container": "wav",
            "sample_rate": 22050
        }
    }
)

result = response.json()
if result["success"]:
    print(f"✅ Audio: {result['audio_url']}")
else:
    print(f"❌ Error: {result['error']['message']}")
```

---

#### Ví dụ 2: Cartesia (Cần API key)

**Curl:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "cartesia",
    "model": "sonic-3",
    "text": "Nhiều thông điệp quan trọng về vai trò của Quốc hội trong khóa mới.",
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
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    json={
        "provider": "cartesia",
        "model": "sonic-3",
        "text": "Nhiều thông điệp quan trọng về vai trò của Quốc hội.",
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
)

result = response.json()
print(result)
```

**Response (Success):**
```json
{
  "success": true,
  "text": "Nhiều thông điệp quan trọng...",
  "audio_url": "/home/nampv1/.../gateway_output/cartesia_Nhiều_thông_điệp_20260409_170225.mp3",
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

---

#### Ví dụ 3: Gemini (Cần API key)

**Curl:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "model": "gemini-2.5-flash-preview-tts",
    "text": "Xin chào, đây là giọng nói Gemini.",
    "voice_config": {
      "voice_id": "Kore",
      "language": "vi"
    },
    "audio_config": {
      "container": "wav",
      "sample_rate": 24000
    }
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    json={
        "provider": "gemini",
        "model": "gemini-2.5-flash-preview-tts",
        "text": "Xin chào, đây là giọng nói Gemini.",
        "voice_config": {
            "voice_id": "Kore",
            "language": "vi"
        },
        "audio_config": {
            "container": "wav",
            "sample_rate": 24000
        }
    }
)

result = response.json()
print(result)
```

---

#### Ví dụ 4: ElevenLabs (Cần API key)

**Curl:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "elevenlabs",
    "text": "Hello, this is ElevenLabs voice synthesis.",
    "voice_config": {
      "voice_id": "pNInz6obpgDQGcFmaJgB",
      "language": "en"
    },
    "audio_config": {
      "container": "mp3",
      "sample_rate": 44100
    }
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/tts",
    json={
        "provider": "elevenlabs",
        "text": "Hello, this is ElevenLabs voice synthesis.",
        "voice_config": {
            "voice_id": "pNInz6obpgDQGcFmaJgB",
            "language": "en"
        },
        "audio_config": {
            "container": "mp3",
            "sample_rate": 44100
        }
    }
)

result = response.json()
print(result)
```

---

#### Ví dụ 5: Xiaomi (Voice Cloning) - Dùng endpoint `/clone`

**⚠️ Xiaomi không hỗ trợ `/tts`!** Provider này chỉ hoạt động theo cơ chế **voice cloning**. Bạn phải dùng endpoint **`/clone`** với **multipart form** để upload file audio mẫu.

Xem chi tiết tại mục **2.6 POST /clone** bên dưới.

---

#### Response Error Example

**Khi provider không tồn tại:**
```json
{
  "success": false,
  "text": "Hello",
  "audio_url": null,
  "provider": "invalid_provider",
  "error": {
    "message": "Provider 'invalid_provider' not available",
    "detail": "Available providers: ['cartesia', 'gemini', 'gtts', ...]"
  }
}
```

**Khi synthesis thất bại:**
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

---

### 2.6 Get Audio - Lấy file audio

**Endpoint:** `GET /audio/{filename}`

**Mô tả:** Tải file audio đã tổng hợp

**Parameters:**
- `filename`: Tên file audio (bao gồm extension)

**Curl:**
```bash
# Tổng hợp trước
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"provider": "gtts", "text": "Hello"}' \
  -o result.json

# Lấy tên file từ response và download
# (Trong thực tế, parse JSON để lấy audio_url)
curl http://localhost:8000/audio/gtts_Hello_20260409_170225.wav \
  -o output.wav
```

**Python:**
```python
import requests

# Bước 1: Tổng hợp
response = requests.post(
    "http://localhost:8000/tts",
    json={"provider": "gtts", "text": "Hello world"}
)
result = response.json()

if result["success"]:
    # Bước 2: Lấy tên file từ audio_url
    audio_path = result["audio_url"]  # e.g., "/path/to/gtts_Hello_...wav"
    filename = audio_path.split("/")[-1]
    
    # Bước 3: Download audio
    audio_response = requests.get(f"http://localhost:8000/audio/{filename}")
    
    with open("output.wav", "wb") as f:
        f.write(audio_response.content)
    
    print(f"✅ Downloaded: output.wav")
```

---

### 2.6 POST /clone - Voice Cloning (Multipart Form)

**Endpoint:** `POST /clone`

**Mô tả:** Clone giọng nói từ file audio mẫu sử dụng multipart form upload. Endpoint này dành riêng cho các provider hỗ trợ voice cloning như **Xiaomi**, **MiniMax**.

**Lưu ý:** Khác với `/tts` (JSON), endpoint này dùng **multipart/form-data** để upload file.

**Form Fields:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `provider` | ✅ | string | Provider name: `'xiaomi'`, `'minimax_selenium'` |
| `text` | ✅ | string | Text cần tổng hợp |
| `reference_audio` | ✅ | file | File audio mẫu để clone (wav, mp3, m4a,...) |
| `reference_text` | ❌ | string | Transcript của audio mẫu (giúp cải thiện chất lượng) |
| `language` | ❌ | string | Mã ngôn ngữ: `'vi'`, `'en'` |
| `enhance_speech` | ❌ | bool | Tăng cường audio trước khi clone (default: true) |
| `volume` | ❌ | float | Âm lượng 0.0-1.0 |
| `speed` | ❌ | float | Tốc độ 0.5-2.0 |
| `pitch` | ❌ | float | Cao độ giọng |
| `emotion` | ❌ | string | Cảm xúc: `'neutral'`, `'happy'`... |
| `container` | ❌ | string | Định dạng output: `'wav'`, `'mp3'` |
| `sample_rate` | ❌ | int | Sample rate: `22050`, `24000`, `44100` |

**Curl:**

```bash
curl -X POST http://localhost:8000/clone \
  -F "provider=xiaomi" \
  -F "text=Xin chào, đây là giọng nói được clone từ audio mẫu." \
  -F "reference_audio=@/path/to/your/reference.wav" \
  -F "reference_text=Transcript của audio mẫu nếu có" \
  -F "language=vi" \
  -F "enhance_speech=true" \
  -F "container=wav" \
  -F "sample_rate=24000"
```

curl -X 'POST' \
  'http://0.0.0.0:8000/clone' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'pitch=0' \
  -F 'container=wav' \
  -F 'reference_text=' \
  -F 'reference_audio=@hn_male_manhdung_full_24k-st.mp3;type=audio/mpeg' \
  -F 'speed=1' \
  -F 'model=' \
  -F 'text=Tổng công ty sẽ tăng cường theo dõi, đánh giá cán bộ theo tuần, tháng, quý và kịp thời điều chỉnh nếu không đáp ứng yêu cầu, đồng thời yêu cầu tập thể lãnh đạo các đơn vị phải giữ vững đoàn kết nội bộ, phát huy truyền thống của người Bưu điện. “Tập thể lao động quản lý tại đơn vị phải là khối thống nhất, đoàn kết nội bộ, tiếp tục xây dựng và phát huy Văn hóa doanh nghiệp Bưu điện Việt Nam, phát huy bản lĩnh chính trị, truyền thống của người bưu điện thì mới đạt được những thắng lợi cùng Bưu điện Việt Nam” - Tổng Giám đốc nhấn mạnh.' \
  -F 'provider=xiaomi' \
  -F 'enhance_speech=true' \
  -F 'sample_rate=24000' \
  -F 'language=vi' \
  -F 'volume=1' \
  -F 'emotion=string'

**Python:**

```python
import requests

# Mở file audio để upload
with open("/path/to/reference.wav", "rb") as f:
    files = {
        "reference_audio": ("reference.wav", f, "audio/wav")
    }
    
    data = {
        "provider": "xiaomi",
        "text": "Xin chào, đây là giọng nói được clone.",
        "reference_text": "Transcript của audio mẫu (nếu có)",
        "language": "vi",
        "enhance_speech": "true",
        "container": "wav",
        "sample_rate": "24000"
    }
    
    response = requests.post(
        "http://localhost:8000/clone",
        files=files,
        data=data
    )

result = response.json()
if result["success"]:
    print(f"✅ Cloned audio: {result['audio_url']}")
else:
    print(f"❌ Clone failed: {result['error']['message']}")
```

**Response (Success):**

```json
{
  "success": true,
  "text": "Xin chào, đây là giọng nói được clone.",
  "audio_url": "/home/nampv1/.../gateway_output/xiaomi_Xin_chào_20260409_180515.wav",
  "provider": "xiaomi",
  "model": "OmniVoice",
  "effective_voice_config": {
    "reference_audio": "/.../ref_xiaomi_20260409_180515.wav",
    "language": "vi",
    "enhance_speech": true
  },
  "effective_audio_config": {
    "container": "wav",
    "sample_rate": 24000
  }
}
```

**Response (Error - thiếu reference_audio):**

```json
{
  "success": false,
  "text": "...",
  "audio_url": null,
  "provider": "xiaomi",
  "error": {
    "message": "Voice cloning not supported",
    "detail": "Provider does not support clone_with_metadata()"
  }
}
```

---

### 2.7 Get Audio - Lấy file audio

**Endpoint:** `GET /audio/{filename}`

**Mô tả:** Tải file audio đã tổng hợp (dùng cho cả `/tts` và `/clone`)

*(Phần này giữ nguyên như cũ, chỉ đổi số section)*

---

### 2.8 Register Provider - Đăng ký provider mới

**Endpoint:** `POST /providers/{provider_name}/register`

**Mô tả:** Đăng ký một provider instance mới với config tùy chỉnh

**Curl:**
```bash
curl -X POST http://localhost:8000/providers/cartesia/register \
  -H "Content-Type: application/json" \
  -d '{
    "api_keys": ["your-api-key-here"],
    "model": "sonic-3"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/providers/cartesia/register",
    json={
        "api_keys": ["your-api-key-here"],
        "model": "sonic-3"
    }
)

print(response.json())
```

**Response:**
```json
{
  "success": true,
  "message": "Provider 'cartesia' registered successfully"
}
```

---

## 3. Script mẫu đầy đủ

### Script Python tổng hợp nhiều đoạn văn bản

```python
#!/usr/bin/env python3
"""Script mẫu: Tổng hợp nhiều đoạn văn bản với nhiều providers"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Danh sách text cần tổng hợp
texts = [
    "Xin chào quý khách.",
    "Cảm ơn bạn đã sử dụng dịch vụ.",
    "Hẹn gặp lại quý khách.",
]

def synthesize_with_provider(text, provider, model=None, voice_config=None):
    """Tổng hợp text với provider chỉ định"""
    
    payload = {
        "provider": provider,
        "text": text,
        "voice_config": voice_config or {},
        "audio_config": {
            "container": "mp3",
            "sample_rate": 22050
        }
    }
    
    if model:
        payload["model"] = model
    
    response = requests.post(f"{BASE_URL}/tts", json=payload)
    return response.json()

def main():
    results = []
    
    # 1. Tổng hợp với gTTS (miễn phí)
    print("\n🎵 Synthesizing with gTTS...")
    for i, text in enumerate(texts):
        result = synthesize_with_provider(
            text=text,
            provider="gtts",
            voice_config={"voice_id": "vi", "language": "vi"}
        )
        results.append(("gTTS", text, result))
        
        if result["success"]:
            print(f"  ✅ [{i+1}/{len(texts)}] {text[:30]}...")
        else:
            print(f"  ❌ [{i+1}/{len(texts)}] Error: {result['error']['message']}")
    
    # 2. Tổng hợp với Cartesia (cần API key)
    print("\n🎵 Synthesizing with Cartesia...")
    for i, text in enumerate(texts[:2]):  # Chỉ tổng hợp 2 đoạn đầu
        result = synthesize_with_provider(
            text=text,
            provider="cartesia",
            model="sonic-3",
            voice_config={
                "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
                "language": "vi",
                "speed": 1.0,
                "emotion": "neutral"
            }
        )
        results.append(("Cartesia", text, result))
        
        if result["success"]:
            print(f"  ✅ [{i+1}/2] {text[:30]}...")
            print(f"      File: {result['audio_url']}")
        else:
            print(f"  ❌ [{i+1}/2] Error: {result['error']['message']}")
    
    # 3. In summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    success_count = sum(1 for _, _, r in results if r["success"])
    total_count = len(results)
    
    for provider, text, result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} [{provider:10}] {text[:40]}...")
    
    print(f"\nTotal: {success_count}/{total_count} successful")

if __name__ == "__main__":
    main()
```

---

## 4. Bảng Voice IDs

| Provider | Voice IDs | Notes |
|----------|-----------|-------|
| **gTTS** | `vi` | Chỉ hỗ trợ tiếng Việt |
| **Cartesia** | `0e58d60a-2f1a-4252-81bd-3db6af45fb41` | Sonic 3 Vietnamese |
| **Gemini** | `Kore`, `Jade`, `Nova`, `Coral`, `Ash` | Prebuilt voices |
| **ElevenLabs** | `pNInz6obpgDQGcFmaJgB` | Rachel voice |
| **Xiaomi** | `cloned` | Voice cloning, không có prebuilt |
| **VNPost** | `Hà My`, `Minh Quang` | Tiếng Việt |

---

## 5. Xử lý lỗi thường gặp

### Lỗi 1: Provider chưa đăng ký
```
Error: Provider 'cartesia' not available
```
**Fix:** Đảm bảo API key được set hoặc provider được đăng ký trong config

### Lỗi 2: API key thiếu
```
Error: No Cartesia API key provided
```
**Fix:** Set environment variable hoặc đăng ký provider với config

### Lỗi 3: Rate limit
```
Error: 429 RESOURCE_EXHAUSTED
```
**Fix:** Chờ giữa các requests hoặc nâng cấp plan

---

## 6. Tài liệu tự động (Swagger)

Khi Gateway đang chạy, truy cập:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Cung cấp giao diện interactive để test tất cả endpoints.
