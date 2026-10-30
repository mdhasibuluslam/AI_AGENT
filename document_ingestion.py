
from __future__ import annotations

MAX_DOCUMENT_CHARS = 200_000
DEFAULT_CHUNK_SIZE = 1_000
DEFAULT_CHUNK_OVERLAP = 150


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split extracted document text into overlapping text chunks."""

    if not isinstance(text, str):
        raise ValueError("Document text must be a string.")

    text = text.strip()

    if not text:
        raise ValueError("Document text cannot be empty.")

    if len(text) > MAX_DOCUMENT_CHARS:
        raise ValueError("Document text exceeds the maximum allowed size.")

    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int):
        raise ValueError("chunk_size must be an integer.")

    if isinstance(overlap, bool) or not isinstance(overlap, int):
        raise ValueError("overlap must be an integer.")

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size.")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks
