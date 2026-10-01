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
