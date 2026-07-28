from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class DocumentPage:
    text: str
    source: str
    page: int


class UnsupportedFileTypeError(ValueError):
    """Raised when a file type is not supported by the loader."""


def _clean_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\x00", "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("The text file could not be decoded.")


def load_document(filename: str, data: bytes) -> list[DocumentPage]:
    """Extract text from a PDF, TXT, or Markdown file while retaining page metadata."""

    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(data))
        pages: list[DocumentPage] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = _clean_text(page.extract_text() or "")
            if text:
                pages.append(DocumentPage(text=text, source=filename, page=page_number))
        return pages

    if suffix in {".txt", ".md", ".markdown"}:
        text = _clean_text(_decode_text(data))
        return [DocumentPage(text=text, source=filename, page=1)] if text else []

    raise UnsupportedFileTypeError(
        f"Unsupported file type {suffix or '(none)'}. Use PDF, TXT, or Markdown."
    )
