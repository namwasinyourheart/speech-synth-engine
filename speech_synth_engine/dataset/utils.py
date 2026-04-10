import uuid
import hashlib
from pathlib import Path

from rich import print

def save_list_to_txt(list, path):
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for item in list:
            f.write(f"{item}\n")

def load_list_from_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def save_items_to_tsv_txt(items, out_path):
    """
    Save (text_id, text) items to a .txt file
    with format: <text_id>\t<text> per line.
    """

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        for text_id, text in items:
            f.write(f"{text_id}\t{text}\n")

    return str(out_p)

def load_items_from_tsv_txt(path):
    """
    Load (text_id, text) items từ file .txt (TSV format)

    Returns:
        list[tuple[str, str]]
    """
    items = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line:
                continue  # skip dòng rỗng

            parts = line.split("\t", 1)  # split 1 lần thôi
            if len(parts) != 2:
                raise ValueError(f"Invalid line format: {line}")

            text_id, text = parts
            items.append((text_id, text))

    return items



def generate_text_ids(
    texts,
    method="hash",      # "uuid" | "incremental" | "hash"
    prefix=None,
    start=1,
    pad=None
):
    ids = []

    for i, text in enumerate(texts, start=start):
        if method == "uuid":
            tid = str(uuid.uuid4())

        elif method == "incremental":
            num = str(i)
            if pad:
                num = num.zfill(pad)
            tid = num

        elif method == "hash":
            tid = hashlib.md5(text.encode()).hexdigest()[:8]

        else:
            raise ValueError("method must be: uuid | incremental | hash")

        if prefix:
            tid = f"{prefix}_{tid}"

        ids.append(tid)

    return ids

def deduplicate_texts(texts, keep="first", return_indices=False):
    """
    Deduplicate list texts, giữ thứ tự.

    Args:
        texts: list[str]
        keep: "first" | "last"
        return_indices: nếu True trả thêm index được giữ

    Returns:
        list[str] hoặc (list[str], list[int])
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    index_map = {}

    if keep == "first":
        for i, t in enumerate(texts):
            if t not in index_map:
                index_map[t] = i
    else:  # last
        for i, t in enumerate(texts):
            index_map[t] = i

    indices = sorted(index_map.values())
    deduped = [texts[i] for i in indices]

    if return_indices:
        return deduped, indices
    return deduped

def make_text_items(
    texts,
    text_ids=None,
    deduplicate=False,
    keep="first",   # "first" | "last"
    **id_kwargs
):
    # Deduplicate texts nếu cần
    if deduplicate:
        texts, indices = deduplicate_texts(
            texts, keep=keep, return_indices=True
        )
        if text_ids is not None:
            text_ids = [text_ids[i] for i in indices]

    # Generate IDs nếu chưa có
    if text_ids is None:
        text_ids = generate_text_ids(texts, **id_kwargs)

    if len(text_ids) != len(texts):
        raise ValueError("text_ids và texts phải cùng độ dài")

    return list(zip(text_ids, texts))



if __name__ == "__main__":
    texts = ["a", "b", "a", "c"]
    # print(generate_text_ids(texts))
    # print(generate_text_ids(texts, method="incremental", pad=5))
    # print(generate_text_ids(texts, method="hash"))


    text_items = make_text_items(texts, method="uuid", prefix=None, pad=3, deduplicate=True, keep="first")
    print(text_items)


