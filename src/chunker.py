from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.document_loader import DocumentPage


@dataclass(frozen=True)
class TextChunk:
    id: str
    text: str
    source: str
    page: int
    chunk_index: int


def _find_breakpoint(text: str, start: int, ideal_end: int) -> int:
    """Prefer paragraph, sentence, then word boundaries near the desired chunk end."""

    if ideal_end >= len(text):
        return len(text)

    search_start = max(start + 1, ideal_end - 180)
    window = text[search_start:ideal_end]
    candidates = [
        window.rfind("\n\n"),
        window.rfind(". "),
        window.rfind("? "),
        window.rfind("! "),
        window.rfind("; "),
        window.rfind(" "),
    ]
    best = max(candidates)
    return search_start + best + 1 if best >= 0 else ideal_end


def chunk_pages(
    pages: list[DocumentPage],
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    chunks: list[TextChunk] = []

    for page in pages:
        text = page.text.strip()
        start = 0
        chunk_index = 0

        while start < len(text):
            ideal_end = min(start + chunk_size, len(text))
            end = _find_breakpoint(text, start, ideal_end)
            chunk_text = text[start:end].strip()

            if chunk_text:
                digest = hashlib.sha256(
                    f"{page.source}|{page.page}|{chunk_index}|{chunk_text}".encode("utf-8")
                ).hexdigest()[:24]
                chunks.append(
                    TextChunk(
                        id=digest,
                        text=chunk_text,
                        source=page.source,
                        page=page.page,
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1

            if end >= len(text):
                break

            next_start = max(0, end - overlap)
            if next_start <= start:
                next_start = end
            start = next_start

    return chunks
