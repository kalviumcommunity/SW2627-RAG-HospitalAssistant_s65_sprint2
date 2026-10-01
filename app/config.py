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


RAW_DATA_DIR = _path_from_env("RAW_DATA_DIR", "data/raw")
PROCESSED_DATA_DIR = _path_from_env("PROCESSED_DATA_DIR", "data/processed")
VECTOR_STORE_PATH = _path_from_env("VECTOR_STORE_PATH", "data/processed/vector_store.json")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")
