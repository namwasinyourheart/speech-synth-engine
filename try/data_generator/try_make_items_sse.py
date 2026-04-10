import sys
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print

from speech_synth_engine.dataset.utils import load_list_from_txt, save_list_to_txt, make_text_items, save_items_to_tsv_txt, load_items_from_tsv_txt

txt_path = "/home/nampv1/projects/tts/speech-synth-engine/examples/example_data/provinces.txt"
texts = load_list_from_txt(txt_path)
text_items = make_text_items(texts, method="incremental", prefix=None, pad=3, deduplicate=True, keep="first")
print(text_items)
# save_list_to_txt(text_items, "/home/nampv1/projects/tts/speech-synth-engine/try/try_output/provinces_items.txt")
save_items_to_tsv_txt(text_items, "/home/nampv1/projects/tts/speech-synth-engine/try/try_output/provinces_items.txt")

items = load_items_from_tsv_txt("/home/nampv1/projects/tts/speech-synth-engine/try/try_output/provinces_items.txt")
print(items)
