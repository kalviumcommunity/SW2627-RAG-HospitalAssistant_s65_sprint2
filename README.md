# Hospital Knowledge Assistant

Educational retrieval pipeline for approved, non-sensitive hospital documents.

This first phase covers document ingestion, cleaning, chunking, metadata,
embeddings, local vector storage, retrieval, and retrieval evaluation. It does
not generate clinical answers or provide patient-specific medical advice.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
```

Keep API keys in `.env`; never commit that file or real patient data.

## Current layout

```text
app/       Pipeline code grouped by stage
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

```text
Documents -> Loader -> Cleaner -> Chunker -> Metadata -> Embeddings
		  -> Vector Store -> Retriever -> Retrieval Service
```

LLM answer generation, grounded prompting, citations in generated answers,
backend API, chat UI, and deployment are intentionally not implemented in this
phase. This is an educational MVP and does not claim clinical accuracy.
