from datetime import datetime
import os

def get_gemini_vertex_ai_client(credentials_path, project_id, location=None):
    """
    Utility: Create and return a Gemini Vertex AI client using service_account.Credentials and genai.Client.
    If location is None or falsy, default to 'us-central1'.
    """
    if not location:
        location = 'us-central1'
    from google.oauth2 import service_account
    from google import genai
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    client = genai.Client(
        credentials=credentials,
        vertexai=True,
        project=project_id,
        location=location
    )
    return client

def get_gemini_api_key_client(api_key: str):
    """
    Utility: Create and return a Gemini client using a direct API key (dev mode).
    """
    if not api_key or not str(api_key).strip():
        raise ValueError("API key is required")
    from google import genai
    return genai.Client(api_key=str(api_key).strip())

def resolve_api_key_from_credentials(credentials_cfg, env_fallback: str = 'GEMINI_API_KEY') -> str | None:
    """
    Resolve the first usable API key from a CredentialsConfig-like object.
    Priority:
    1) credentials_cfg.api_keys (str or list) -> first non-empty trimmed
    2) First non-empty value from credentials_cfg.envs
    3) Fallback to a common env var name (env_fallback)
    Returns the API key string or None if not found.
    """
    # 1) From api_keys field
    if credentials_cfg is not None:
        k = getattr(credentials_cfg, 'api_keys', None)
        if isinstance(k, str) and k.strip():
            parts = [s for s in (x.strip() for x in k.split(',')) if s]
            if parts:
                return parts[0]
        elif isinstance(k, list):
            for item in k:
                s = str(item).strip()
                if s:
                    return s
        # 2) From envs list
        for env_name in (getattr(credentials_cfg, 'envs', []) or []):
            val = os.getenv(env_name)
            if val and str(val).strip():
                return str(val).strip()

    # 3) Fallback env
    env_key = os.getenv(env_fallback)
    if env_key and str(env_key).strip():
        return str(env_key).strip()
    return None

def extract_vertex_ai_credentials(cred_cfg):
    """
    Helper: chỉ lấy credentials_path, project_id, location từ CredentialsConfig.envs
    với các tên env CHUẨN duy nhất: GCP_CREDENTIALS, GCP_PROJECT_ID, GCP_LOCATION.
    Trả về tuple (credentials_path, project_id, location).
    """
    credentials_path = None
    project_id = None
    location = None
    # Only use exact env names
    for env_name in getattr(cred_cfg, 'envs', []) or []:
        val = os.getenv(env_name)
        if env_name == 'GCP_CREDENTIALS':
            credentials_path = val
        elif env_name == 'GCP_PROJECT_ID':
            project_id = val
        elif env_name == 'GCP_LOCATION':
            location = val
    return credentials_path, project_id, location

def time_to_vietnamese_spoken(time_str):
    dt = datetime.strptime(time_str, "%Y_%m_%d__%H_%M_%S")
    
    day = dt.day
    month = dt.month
    year = dt.year
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    
    return f"Ngày {day} tháng {month} năm {year}, {hour} giờ {minute} phút {second} giây."

# # ví dụ
# s = "2026_04_09__14_05_23"
# print(time_to_vietnamese_spoken(s))