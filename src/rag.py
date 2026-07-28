from __future__ import annotations

from dataclasses import dataclass

from groq import Groq

from src.embeddings import EmbeddingService
from src.vector_store import ChromaVectorStore, RetrievedChunk


@dataclass(frozen=True)
class RAGResponse:
    answer: str
    sources: list[RetrievedChunk]
    retrieved_count: int


SYSTEM_PROMPT = """You are CiteRAG, a grounded document question-answering assistant.

Rules:
1. Answer only from the supplied document context.
2. Cite every factual claim using source markers such as [S1] or [S2].
3. Never invent facts, page numbers, quotations, or citations.
4. If the context is incomplete, explicitly say what is not available.
5. If the context does not answer the question, say: "I could not find enough relevant information in the indexed documents."
6. Keep the answer clear and professional.
"""


def _build_context(chunks: list[RetrievedChunk]) -> str:
    sections: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            f"[S{index}] Source: {chunk.source} | Page: {chunk.page} | "
            f"Relevance: {chunk.relevance:.2f}\n{chunk.text}"
        )
    return "\n\n---\n\n".join(sections)


def answer_question(
    question: str,
    api_key: str,
    model: str,
    embedding_service: EmbeddingService,
    vector_store: ChromaVectorStore,
    top_k: int,
    min_relevance: float,
    conversation_history: list[dict[str, str]] | None = None,
) -> RAGResponse:
    query_embedding = embedding_service.encode_query(question)
    retrieved = vector_store.search(query_embedding, top_k=top_k)
    relevant = [item for item in retrieved if item.relevance >= min_relevance]

    if not relevant:
        return RAGResponse(
            answer=(
                "I could not find enough relevant information in the indexed documents. "
                "Try rephrasing the question, lowering the relevance threshold slightly, "
                "or uploading a document that contains the answer."
            ),
            sources=[],
            retrieved_count=len(retrieved),
        )

    history = (conversation_history or [])[-6:]
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        if item.get("role") in {"user", "assistant"} and item.get("content"):
            messages.append({"role": item["role"], "content": item["content"]})

    messages.append(
        {
            "role": "user",
            "content": (
                f"DOCUMENT CONTEXT:\n{_build_context(relevant)}\n\n"
                f"QUESTION:\n{question}\n\n"
                "Answer using only the context and include [S#] citations."
            ),
        }
    )

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,
        max_tokens=1200,
    )
    answer = completion.choices[0].message.content or "No answer was returned."
    return RAGResponse(
        answer=answer.strip(),
        sources=relevant,
        retrieved_count=len(retrieved),
    )
