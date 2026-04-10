import sys
import os
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))


from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig
from speech_synth_engine.providers.base.provider_factory import ProviderFactory
from rich import print

factory = ProviderFactory()

pcfg = ProviderConfig(
    name="gemini",
    models=["gemini-2.5-flash-preview-tts", "gemini-2.0-pro-tts"],
    default_model="gemini-2.5-flash-preview-tts",
    credentials=CredentialsConfig(
        envs=["GEMINI_API_KEY", "GCP_CREDENTIAL_PATH", "GCP_PROJECT_ID", "GCP_LOCATION"],
        required=["GCP_CREDENTIAL_PATH", "GCP_PROJECT_ID"],
    ),
)

provider = factory.create_provider(
    "gemini",
    config={
        "provider_config": pcfg,   # pass instance, not dict
        # ... other provider config like language, sample_rate if needed
    }
)

# print(provider.get_metadata_info())

provider.synthesize(
    "Xin chào, tôi là gTTS provider",
    "vi",
    "gemini-2.5-flash-preview-tts",
    "/home/nampv1/projects/tts/speech-synth-engine/try/output/try_gemini_1.wav"
)

# from pathlib import Path
# from speech_synth_engine.providers.base.provider_factory import ProviderFactory

# factory = ProviderFactory()
# provider = factory.create_provider(
#     "gemini",
#     config={
#         "sample_rate": 24000,
#         "language": "vi",
#         "provider_config": {
#             "name": "gemini",
#             "models": ["gemini-2.5-flash-preview-tts", "gemini-2.0-pro-tts"],
#             "default_model": "gemini-2.5-flash-preview-tts",
#             "credentials": {
#                 "envs": ["GEMINI_API_KEY", "GCP_CREDENTIAL_PATH", "GCP_PROJECT_ID", "GCP_LOCATION"],
#                 "required": ["GCP_CREDENTIAL_PATH", "GCP_PROJECT_ID"],
#                 "notes": "For Vertex AI mode, set credentials; for API key mode, set GEMINI_API_KEY."
#             }
#         }
#     }
# )
# print(provider.get_metadata_info())