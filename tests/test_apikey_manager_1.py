import sys
sys.path.append("/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.api_keys import APIKeyManager


import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


manager = APIKeyManager("TestProvider", env_var_prefix="GEMINI_API_KEY")
current_key = manager.get_current_key()
print(current_key)


_available_keys = manager._load_api_keys()
print(_available_keys)
