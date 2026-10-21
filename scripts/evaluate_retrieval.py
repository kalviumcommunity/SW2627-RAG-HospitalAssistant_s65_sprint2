"""Evaluate source hit rate for the labelled retrieval query set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import VECTOR_STORE_PATH
from app.embeddings.embedder import Embedder
from app.evaluation.metrics import evaluate_retrieval
from app.retrieval.retriever import Retriever
from app.vector_store.local_store import LocalVectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=Path("data/processed/evaluation_queries.json"))
    parser.add_argument("--store", type=Path, default=VECTOR_STORE_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    cases = json.loads(args.queries.read_text(encoding="utf-8"))
    results = evaluate_retrieval(
        Retriever(Embedder(), LocalVectorStore(args.store)), cases, args.top_k
    )
    print(f"Total queries: {results['total_queries']}")
    print(f"Successful retrievals: {results['successful_retrievals']}")
    print(f"Hit rate: {results['hit_rate']:.0%}")


if __name__ == "__main__":
    main()