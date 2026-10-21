# Hospital Knowledge Assistant

Educational, source-grounded knowledge assistant for approved, non-sensitive hospital documents.

The project now demonstrates ingestion through retrieval, grounded answer
generation, citations, a small backend API, and a browser chat interface.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m pytest
```

Keep API keys in `.env`; never commit that file or real patient data.

## Current layout

```text
app/       Pipeline code grouped by stage
frontend/  Static chat interface
data/raw/  Approved sample input documents
data/processed/ Intermediate JSON/JSONL data
scripts/   Command-line pipeline scripts
tests/     Automated tests
```

## Document ingestion

Place approved, non-sensitive PDF guidelines in `data/raw/`. The loader extracts
one `DocumentPage` record per page and preserves the filename, source path,
document identifier, and one-based page number for later retrieval citations.

Text cleaning trims extraction whitespace, removes null control characters, and
collapses repeated blank lines without rewriting medical terminology. For
example, `"  dose  \\n\\n\\n  500 mg "` becomes `"dose\\n\\n500 mg"`.

## Embeddings

`Embedder` uses the model named by `EMBEDDING_MODEL` and reads `OPENAI_API_KEY`
from `.env`. It accepts batches and converts provider failures into a clear
`EmbeddingError`; tests inject a fake client and do not make network calls.

## Local vector store

`LocalVectorStore` persists vectors, chunk text, and metadata in
`data/processed/vector_store.json`. It is created automatically on first write;
call `clear()` when resetting a local experiment. This JSON store is intended
for the educational MVP, not production clinical workloads.

## Pipeline usage

From the repository root, run `python scripts/index_documents.py` after placing
approved PDFs in `data/raw/`. Retrieval can then be called from Python:

```python
from app.retrieval.service import retrieve_context

results = retrieve_context("What is the drug interaction guidance?", top_k=5)
```

Evaluation runs with `python scripts/evaluate_retrieval.py` and uses the labelled
cases in `data/processed/evaluation_queries.json`.

## Run the assistant

Set `OPENAI_API_KEY` (or the separate `EMBEDDING_API_KEY` and `LLM_API_KEY`)
in an uncommitted `.env` file. Choose models with `EMBEDDING_MODEL` and
`LLM_MODEL`. Index approved documents with:

```bash
python scripts/index_documents.py
```

Start the backend with `python scripts/run_api.py`, then serve `frontend/`
from another terminal with `python -m http.server 8080 --directory frontend`.
Open `http://127.0.0.1:8080`. The API can also be called directly:

```bash
curl -X POST http://127.0.0.1:8000/ask \
	-H "Content-Type: application/json" \
	-d '{"question":"What does the approved guideline say?","top_k":5}'
```

```text
Documents -> Loader -> Cleaner -> Chunker -> Metadata -> Embeddings
		  -> Vector Store -> Retriever -> Retrieval Service
```

```text
Documents -> Loader -> Cleaner -> Chunker -> Metadata -> Embeddings
		  -> Vector Store -> Retriever -> Grounded Prompt -> LLM Answer
		  -> Citations -> Backend API -> Chat UI
```

## Safety and limitations

This project is an educational MVP. It does not provide medical diagnosis,
patient-specific medical advice, automatic treatment decisions, or clinical guarantees.
Answers are limited to retrieved context and citations identify source metadata;
citations do not prove clinical correctness. Conversation history is in-memory
only and is not suitable for production clinical records. Use only approved,
non-sensitive documents and never commit `.env`, API keys, patient data, or
confidential hospital documents.

Production deployment, complex authentication, audit logging, security testing,
clinical validation, compliance review, advanced monitoring, and performance
hardening are intentionally deferred.
