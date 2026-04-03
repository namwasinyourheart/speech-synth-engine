#!/usr/bin/env python3

import sys

sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.schemas.provider import ProviderConfig

cfg = ProviderConfig.from_vertex_ai_defaults(
    name="gemini",
    models=["gemini-2.5-flash-preview-tts", "gemini-2.0-pro-tts"],
    default_model="gemini-2.5-flash-preview-tts",
)

print("Default model:", cfg.default_model)
print("Models:", cfg.models)
print("Credentials:", cfg.credentials)

ok, missing = cfg.credentials.validate_envs(strict=False)
if not ok:
    print("Missing required envs:", missing)
present = cfg.credentials.get_present_envs()
print("Present:", present)