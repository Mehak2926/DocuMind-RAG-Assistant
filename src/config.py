from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    groq_api_key: str
    groq_model: str
    embedding_model: str
    chroma_dir: Path
    collection_name: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_relevance: float


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, received {value!r}.") from exc


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name, str(default))
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, received {value!r}.") from exc


def load_settings() -> Settings:
    chunk_size = _get_int("CHUNK_SIZE", 900)
    chunk_overlap = _get_int("CHUNK_OVERLAP", 150)
    top_k = _get_int("TOP_K", 5)
    min_relevance = _get_float("MIN_RELEVANCE", 0.35)

    if chunk_size < 200:
        raise ValueError("CHUNK_SIZE must be at least 200 characters.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be non-negative and smaller than CHUNK_SIZE.")
    if top_k < 1:
        raise ValueError("TOP_K must be at least 1.")
    if not 0.0 <= min_relevance <= 1.0:
        raise ValueError("MIN_RELEVANCE must be between 0 and 1.")

    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ).strip(),
        chroma_dir=Path(os.getenv("CHROMA_DIR", "data/chroma_db")),
        collection_name=os.getenv("COLLECTION_NAME", "document_qa").strip(),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        min_relevance=min_relevance,
    )
