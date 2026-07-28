from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from src.chunker import chunk_pages
from src.config import load_settings
from src.document_loader import UnsupportedFileTypeError, load_document
from src.embeddings import EmbeddingService
from src.rag import answer_question
from src.vector_store import ChromaVectorStore


st.set_page_config(
    page_title="CiteRAG — Document Q&A",
    page_icon="📚",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 1.8rem;}
      .hero {
        padding: 1.35rem 1.5rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 18px;
        margin-bottom: 1rem;
      }
      .hero h1 {margin: 0 0 .25rem 0; font-size: 2.15rem;}
      .hero p {margin: 0; opacity: .78;}
      .metric-card {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 14px;
        padding: .85rem 1rem;
      }
      .source-chip {
        display: inline-block;
        padding: .18rem .55rem;
        margin: .1rem .2rem .1rem 0;
        border-radius: 999px;
        background: rgba(100,100,100,.12);
        font-size: .82rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_embedding_service(model_name: str) -> EmbeddingService:
    return EmbeddingService(model_name)


@st.cache_resource(show_spinner=False)
def get_vector_store(directory: str, collection_name: str) -> ChromaVectorStore:
    return ChromaVectorStore(directory, collection_name)


def initialize_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("index_report", None)


def render_sources(sources) -> None:
    if not sources:
        return
    st.markdown("**Evidence used**")
    for index, source in enumerate(sources, start=1):
        label = (
            f"S{index} · {source.source} · page {source.page} · "
            f"relevance {source.relevance:.2f}"
        )
        with st.expander(label):
            st.write(source.text)


settings = load_settings()
initialize_state()
vector_store = get_vector_store(str(settings.chroma_dir), settings.collection_name)

st.markdown(
    """
    <div class="hero">
      <h1>📚 CiteRAG</h1>
      <p>Ask questions across your PDFs and text files. Answers are grounded in retrieved passages and include source citations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "Groq API key",
        value=settings.groq_api_key,
        type="password",
        help="Stored only in this Streamlit session unless you put it in .env.",
    )

    supported_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    ]
    default_index = (
        supported_models.index(settings.groq_model)
        if settings.groq_model in supported_models
        else 0
    )
    model = st.selectbox("Groq model", supported_models, index=default_index)
    top_k = st.slider("Retrieved chunks", 1, 10, settings.top_k)
    min_relevance = st.slider(
        "Minimum relevance",
        0.0,
        1.0,
        float(settings.min_relevance),
        0.05,
        help="Chunks below this cosine-similarity score are excluded before generation.",
    )

    st.divider()
    st.caption(f"Embedding model: `{settings.embedding_model}`")
    st.caption(f"Collection: `{settings.collection_name}`")

    if st.button("Clear vector database", use_container_width=True):
        vector_store.clear()
        st.session_state.messages = []
        st.session_state.index_report = None
        st.success("Vector database cleared.")
        st.rerun()

left, right = st.columns([0.38, 0.62], gap="large")

with left:
    st.subheader("1. Add documents")
    uploads = st.file_uploader(
        "Upload PDF, TXT, or Markdown files",
        type=["pdf", "txt", "md", "markdown"],
        accept_multiple_files=True,
    )

    if st.button("Index documents", type="primary", use_container_width=True):
        if not uploads:
            st.warning("Choose at least one document first.")
        else:
            report = {"files": 0, "pages": 0, "chunks": 0, "warnings": []}
            try:
                with st.status("Building the searchable knowledge base...", expanded=True) as status:
                    st.write("Loading the local embedding model...")
                    embedding_service = get_embedding_service(settings.embedding_model)

                    for upload in uploads:
                        st.write(f"Extracting `{upload.name}`...")
                        try:
                            pages = load_document(upload.name, upload.getvalue())
                        except (UnsupportedFileTypeError, ValueError) as exc:
                            report["warnings"].append(f"{upload.name}: {exc}")
                            continue

                        if not pages:
                            report["warnings"].append(
                                f"{upload.name}: no selectable text was found. Scanned PDFs need OCR."
                            )
                            continue

                        chunks = chunk_pages(
                            pages,
                            chunk_size=settings.chunk_size,
                            overlap=settings.chunk_overlap,
                        )
                        st.write(f"Embedding {len(chunks)} chunks from `{upload.name}`...")
                        embeddings = embedding_service.encode_documents(
                            [chunk.text for chunk in chunks]
                        )
                        vector_store.delete_source(upload.name)
                        vector_store.add_chunks(chunks, embeddings)

                        report["files"] += 1
                        report["pages"] += len(pages)
                        report["chunks"] += len(chunks)

                    status.update(label="Indexing complete", state="complete")
                st.session_state.index_report = report
            except Exception as exc:
                st.error(f"Indexing failed: {exc}")

    report = st.session_state.index_report
    if report:
        m1, m2, m3 = st.columns(3)
        m1.metric("Files", report["files"])
        m2.metric("Pages", report["pages"])
        m3.metric("Chunks", report["chunks"])
        for warning in report["warnings"]:
            st.warning(warning)

    st.subheader("Knowledge base")
    st.metric("Stored chunks", vector_store.count())
    sources = vector_store.list_sources()
    if sources:
        st.markdown(
            "".join(f'<span class="source-chip">{source}</span>' for source in sources),
            unsafe_allow_html=True,
        )
    else:
        st.caption("No documents indexed yet.")

with right:
    st.subheader("2. Ask questions")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))

    question = st.chat_input("Ask something that is answered by your documents...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            if not api_key:
                answer = "Add your Groq API key in the sidebar or in the `.env` file."
                st.error(answer)
                response_sources = []
            elif vector_store.count() == 0:
                answer = "Upload and index at least one document before asking a question."
                st.warning(answer)
                response_sources = []
            else:
                try:
                    with st.spinner("Retrieving evidence and generating a grounded answer..."):
                        embedding_service = get_embedding_service(settings.embedding_model)
                        response = answer_question(
                            question=question,
                            api_key=api_key,
                            model=model,
                            embedding_service=embedding_service,
                            vector_store=vector_store,
                            top_k=top_k,
                            min_relevance=min_relevance,
                            conversation_history=st.session_state.messages[:-1],
                        )
                    answer = response.answer
                    response_sources = response.sources
                    st.markdown(answer)
                    render_sources(response_sources)
                except Exception as exc:
                    answer = f"The request failed: {exc}"
                    response_sources = []
                    st.error(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "sources": response_sources}
        )
