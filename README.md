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
PDF files under `data/raw/` are intentionally ignored by Git. Keep downloaded
WHO or hospital documents local unless their redistribution is explicitly approved.

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

`Embedder` uses the local `all-MiniLM-L6-v2` model by default. The model is
downloaded once by `sentence-transformers` and then runs locally; embedding
does not use Gemini quota or an API key. It accepts batches and converts model
failures into a clear `EmbeddingError`; tests inject a fake client and do not
download a model.

For the free Render service, `render.yaml` selects `EMBEDDING_MODEL=hash-384`.
This dependency-free hashed embedding avoids loading PyTorch on the 512 MB
free instance. It is suitable for the educational demo but generally gives
less semantic retrieval than MiniLM. Set `EMBEDDING_MODEL=all-MiniLM-L6-v2`
when running locally or on a larger instance.

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

Set `GEMINI_API_KEY` in an uncommitted `.env` file for answer generation.
Choose the local embedding model with `EMBEDDING_MODEL` and Gemini's answer
model with `LLM_MODEL`. Index approved documents with:

```bash
python scripts/index_documents.py
```

For the demo, indexing defaults to the first PDF and all its pages. Set
`MAX_DOCUMENTS=2` or `MAX_PAGES=20` when a smaller demo index is preferred.
Local indexing does not consume Gemini embedding quota. Retrieval uses seven
passages so broad overview questions can include introductory material, and
generated answers are limited to 512 tokens.

Start the backend with `python scripts/run_api.py`, then serve `frontend/`
from another terminal with `python -m http.server 8080 --directory frontend`.
Open `http://127.0.0.1:8080`. The API can also be called directly:

```bash
curl -X POST http://127.0.0.1:8000/ask \
	-H "Content-Type: application/json" \
	-d '{"question":"What does the approved guideline say?","top_k":5}'
```

## Upload and update documents

The browser includes an upload panel for approved, non-sensitive PDF files.
Uploading a new filename adds it to the local index; uploading the same
filename replaces its previous indexed version. The local embedding model runs
on the server, so uploads do not consume Gemini embedding quota.

The API also exposes:

```text
GET  /documents
POST /documents/upload
DELETE /documents/{document_name}
POST /documents/rebuild
```

Indexing runs synchronously for this educational demo. The upload status stays
visible while pages are extracted and local embeddings are created. Questions
remain fast after indexing because the cached local model and vector store are
reused. The default upload limit is 25 MB; configure `MAX_UPLOAD_BYTES` for a
different limit.

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

The API currently adds request identifiers and basic browser security headers,
and returns generic internal errors without exposing implementation details.

## Deploy a mentor demo on Render

The repository includes [`render.yaml`](./render.yaml) for separate Render
services: a Python API and a static frontend. Create a new Render Blueprint
from this repository and provide these values when prompted:

- `GEMINI_API_KEY`: your Gemini key, entered only in Render
- `BACKEND_URL` on the frontend service: the deployed API URL
- `CORS_ORIGINS` on the API service: the deployed frontend URL

Render supplies `PORT`; the API binds to `0.0.0.0` automatically in deployment.
The local embedding model downloads during the API build/first use, so the
first request can be slower. Uploaded files and the JSON vector store require
persistent disk if they must survive a service restart; a free ephemeral
instance is suitable only for a live mentor demonstration. Upload the PDF
after deployment, wait for the indexing success message, and then ask questions.
