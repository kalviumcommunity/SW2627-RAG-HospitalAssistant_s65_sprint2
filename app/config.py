"""Application settings loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _path_from_env(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _origin_from_env(value: str) -> str:
    origin = value.strip().rstrip("/")
    if origin and not origin.startswith(("http://", "https://")):
        return f"https://{origin}"
    return origin


RAW_DATA_DIR = _path_from_env("RAW_DATA_DIR", "data/raw")
PROCESSED_DATA_DIR = _path_from_env("PROCESSED_DATA_DIR", "data/processed")
VECTOR_STORE_PATH = _path_from_env("VECTOR_STORE_PATH", "data/processed/vector_store.json")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS", "100"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "0"))
INDEX_CHUNK_SIZE = int(os.getenv("INDEX_CHUNK_SIZE", "3000"))
INDEX_CHUNK_OVERLAP = int(os.getenv("INDEX_CHUNK_OVERLAP", "200"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "7"))
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "512"))
LLM_TIMEOUT_MS = int(os.getenv("LLM_TIMEOUT_MS", "15000"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or GEMINI_API_KEY
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
LLM_API_KEY = os.getenv("LLM_API_KEY") or GEMINI_API_KEY
CORS_ORIGINS = [
    _origin_from_env(origin)
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if origin.strip()
]
