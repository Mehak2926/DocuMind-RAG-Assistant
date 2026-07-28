from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb

from src.chunker import TextChunk


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    page: int
    chunk_index: int
    relevance: float


class ChromaVectorStore:
    """Persistent local Chroma store using cosine distance."""

    def __init__(self, persist_directory: Path | str, collection_name: str) -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=None,
                configuration={"hnsw": {"space": "cosine"}},
            )
        except TypeError:
            # Compatibility fallback for older Chroma releases.
            return self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=None,
                metadata={"hnsw:space": "cosine"},
            )

    def count(self) -> int:
        return int(self.collection.count())

    def list_sources(self) -> list[str]:
        if self.count() == 0:
            return []
        result = self.collection.get(include=["metadatas"])
        metadatas = result.get("metadatas") or []
        return sorted({str(meta.get("source", "Unknown")) for meta in metadatas})

    def delete_source(self, source: str) -> None:
        self.collection.delete(where={"source": source})

    def add_chunks(
        self,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have exactly one embedding.")
        if not chunks:
            return

        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "source": chunk.source,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if self.count() == 0:
            return []

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=False):
            # With cosine space, Chroma distance = 1 - cosine similarity.
            relevance = max(0.0, min(1.0, 1.0 - float(distance)))
            retrieved.append(
                RetrievedChunk(
                    text=str(text),
                    source=str(metadata.get("source", "Unknown")),
                    page=int(metadata.get("page", 1)),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    relevance=relevance,
                )
            )
        return retrieved

    def clear(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self._get_or_create_collection()
