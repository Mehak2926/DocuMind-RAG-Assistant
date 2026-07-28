# 🤖 DocuMind RAG Assistant

An AI-powered document question-answering system built using Retrieval-Augmented Generation (RAG).

The application allows users to upload PDF documents and ask questions. The system retrieves relevant document sections and generates grounded answers with citations.

## 🚀 Features

- PDF and text document ingestion
- Intelligent document chunking
- Sentence Transformer embeddings
- ChromaDB vector database
- Groq LLM integration
- Source-based answers with citations
- Relevance score filtering to reduce hallucination

## 🏗️ Architecture

User Query  
↓  
Embedding Generation  
↓  
Vector Search (ChromaDB)  
↓  
Relevant Context Retrieval  
↓  
LLM Generation (Groq)  
↓  
Answer + Sources

## 🛠️ Technologies

- Python
- Streamlit
- LangChain-style RAG pipeline
- ChromaDB
- Sentence Transformers
- Groq API

## ▶️ Run Locally

```bash
git clone https://github.com/Mehak2926/DocuMind-RAG-Assistant.git

cd DocuMind-RAG-Assistant

pip install -r requirements.txt

streamlit run app.py
