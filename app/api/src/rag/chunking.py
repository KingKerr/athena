import re
from typing import List


DEFAULT_TARGET_CHARS = 1200
DEFAULT_OVERLAP_CHARS = 200
DEFAULT_MIN_CHARS = 300


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    parts = re.split(r"(?<=[\.\!\?\;\:])\s+|\n{2,}", text)
    parts = [p.strip() for p in parts if p and p.strip()]
    return parts


def fallback_split(text: str, target_chars: int, overlap_chars: int) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    step = max(1, target_chars - overlap_chars)

    while start < len(text):
        end = min(len(text), start + target_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def chunk_text(
    text: str,
    target_chars: int = DEFAULT_TARGET_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    sentences = split_sentences(text)
    if not sentences:
        return fallback_split(text, target_chars, overlap_chars)

    chunks = []
    current = []

    for sentence in sentences:
        candidate = " ".join(current + [sentence]).strip()

        if current and len(candidate) > target_chars:
            chunk = " ".join(current).strip()
            if chunk:
                chunks.append(chunk)

            overlap = []
            overlap_len = 0
            for s in reversed(current):
                overlap.insert(0, s)
                overlap_len += len(s) + 1
                if overlap_len >= overlap_chars:
                    break

            current = overlap + [sentence]
        else:
            current.append(sentence)

    if current:
        chunk = " ".join(current).strip()
        if chunk:
            chunks.append(chunk)

    merged = []
    for chunk in chunks:
        if merged and len(chunk) < min_chars:
            merged[-1] = f"{merged[-1]} {chunk}".strip()
        else:
            merged.append(chunk)

    if not merged:
        return fallback_split(text, target_chars, overlap_chars)

    return merged