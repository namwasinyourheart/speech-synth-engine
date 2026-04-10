# Hướng dẫn sử dụng GeminiTTSProvider với Vertex AI

## 1. Đảm bảo cài đặt các package cần thiết
```bash
pip install google-generativeai google-auth
```

## 2. Chuẩn bị file credentials (service account) của Google Cloud
- Tạo service account và tải file JSON credentials từ Google Cloud Console.

## 3. Cấu hình provider với providerconfig/credentialconfig
Bạn nên ưu tiên truyền thông tin credentials qua providerconfig dạng schema chuẩn. Ví dụ:

```python
from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig
from speech_synth_engine.providers.gemini_provider import GeminiTTSProvider

provider_config = ProviderConfig(
    name="gemini-vertex",
    models=["gemini-2.5-flash-preview-tts"],
    default_model="gemini-2.5-flash-preview-tts",
    credentials=CredentialsConfig(
        envs=["GCP_CREDENTIALS_PATH", "GCP_PROJECT_ID", "GCP_LOCATION"],
        required=["GCP_CREDENTIALS_PATH", "GCP_PROJECT_ID"],
        api_keys=["/path/to/your/credentials.json"],
        notes="Đặt các biến môi trường hoặc truyền trực tiếp đường dẫn credentials và project_id."
    )
)

import os
os.environ["GCP_CREDENTIALS_PATH"] = "/path/to/your/credentials.json"
os.environ["GCP_PROJECT_ID"] = "your-gcp-project-id"

provider = GeminiTTSProvider(
    name="gemini-vertex",
    config={
        "use_vertex_ai": True,
        "provider_config": provider_config
    }
)
```

## 4. Nếu không dùng providerconfig, có thể truyền trực tiếp trong config:
```python
provider = GeminiTTSProvider(
    name="gemini-vertex",
    config={
        "use_vertex_ai": True,
        "credentials_path": "/path/to/your/credentials.json",
        "project_id": "your-gcp-project-id",
        "location": "us-central1"
    }
)
```

## 5. Lưu ý
- Nếu dùng providerconfig, các trường credentials sẽ được ưu tiên lấy từ envs/required/api_keys của ProviderConfig.
- Nếu không tìm thấy, sẽ fallback sang config truyền vào.
- Đảm bảo file credentials và project_id hợp lệ, có quyền truy cập Vertex AI.

## 6. Ví dụ synthesize
```python
provider.synthesize(
    text="Xin chào, đây là test Gemini Vertex AI!",
    output_file="output.wav",
    generation_config=None
)
```
