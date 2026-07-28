# CiteRAG — Document Q&A Assistant

A portfolio-ready Retrieval-Augmented Generation application. It ingests PDF, TXT, and Markdown documents, creates local sentence-transformer embeddings, stores them persistently in Chroma, retrieves relevant passages, and asks a Groq-hosted LLM to answer with inline citations.

## Features

- Multi-file PDF/TXT/Markdown upload
- Page-aware PDF extraction
- Configurable chunk size and overlap
- Free local embeddings with `sentence-transformers/all-MiniLM-L6-v2`
- Persistent Chroma vector database
- Cosine-similarity relevance threshold to reduce hallucination
- Groq chat completion using production models
- Inline `[S1]`, `[S2]` citations and expandable source passages
- Duplicate-safe document re-indexing
- Clean Streamlit chat interface
- Sample Etsy operations document
- Basic tests, Dockerfile, Windows launcher, and Linux/macOS launcher

## Architecture

```text
Upload documents
      ↓
Text extraction with page metadata
      ↓
Overlapping chunks
      ↓
Sentence-Transformer embeddings (local)
      ↓
Persistent Chroma cosine index
      ↓
Top-k retrieval + relevance threshold
      ↓
Grounded Groq prompt
      ↓
Answer with source citations
```

## Project structure

```text
CiteRAG-Groq/
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── run.bat
├── run.sh
├── src/
│   ├── config.py
│   ├── document_loader.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   └── rag.py
├── sample_docs/
│   └── etsy_seller_guide.txt
├── tests/
└── data/chroma_db/
```

## Run in VS Code on Windows

### 1. Install Python

Use Python 3.10 or 3.11. During installation, enable **Add Python to PATH**.

### 2. Open the project

Extract the ZIP, open VS Code, and choose **File → Open Folder → CiteRAG-Groq**.

### 3. Create a virtual environment

In the VS Code terminal:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4. Install packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The first run downloads the embedding model. This can take longer than later runs.

### 5. Add your Groq key

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace:

```env
GROQ_API_KEY=gsk_your_key_here
```

Never upload `.env` to GitHub.

### 6. Start the app

```powershell
python -m streamlit run app.py
```

Or simply double-click `run.bat`. It creates the environment, installs dependencies, copies `.env.example`, and starts the app.

Open the local URL displayed in the terminal, normally `http://localhost:8501`.

## How to use

1. Upload one or more PDFs, text files, or Markdown files.
2. Select **Index documents**.
3. Wait for extraction, chunking, embedding, and storage to finish.
4. Ask a question whose answer appears in the documents.
5. Review the inline citations and expand the evidence passages.
6. Raise the minimum relevance threshold for stricter grounding; lower it if valid passages are being excluded.

## Important limitations

- Scanned/image-only PDFs need OCR before this app can read them.
- Retrieval quality depends on document quality, chunk settings, and the embedding model.
- A relevance threshold reduces unsupported generation but cannot guarantee perfect accuracy.
- Do not use the application as a substitute for professional legal, medical, or financial advice.

## Run tests

```powershell
pip install -r requirements-dev.txt
pytest -q
```

## Docker

```bash
docker build -t citerag .
docker run --env-file .env -p 8501:8501 citerag
```

## Strong resume bullet

> Built a retrieval-augmented generation (RAG) document assistant that extracts PDF/text content, applies overlapping chunking, creates normalized Sentence-Transformer embeddings, persists vectors in Chroma, and generates Groq-powered answers with page-level source citations. Added cosine-similarity thresholding and grounded prompting to reduce hallucinations.

## Interview talking points

- Why overlapping chunks improve context continuity
- Why cosine similarity is appropriate for normalized text embeddings
- Precision/recall trade-off when changing `TOP_K` and `MIN_RELEVANCE`
- Why retrieval is performed before generation
- How citations make answers auditable
- How you would add OCR, reranking, hybrid search, evaluation datasets, authentication, and cloud deployment
