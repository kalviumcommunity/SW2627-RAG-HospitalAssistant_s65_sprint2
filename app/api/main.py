"""Small API composition layer for retrieval, generation, and citations."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.generation.answer_generator import AnswerGenerationError, AnswerGenerator
from app.generation.citations import attach_citations
from app.retrieval.service import RetrievalServiceError, retrieve_context


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


def create_app(
    retrieve: Callable[[str, int], list[dict[str, Any]]] = retrieve_context,
    generate: Callable[[str, list[dict[str, Any]]], str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Hospital Knowledge Assistant")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask")
    def ask(request: AskRequest) -> dict[str, Any]:
        try:
            chunks = retrieve(request.question, request.top_k)
        except RetrievalServiceError as error:
            raise HTTPException(status_code=503, detail="retrieval is temporarily unavailable") from error
        if not chunks:
            return attach_citations(
                "The supplied documents do not contain enough information to answer this question.", []
            )
        try:
            if generate:
                answer = generate(request.question, chunks)
            else:
                answer = AnswerGenerator().generate(request.question, chunks)
        except AnswerGenerationError as error:
            raise HTTPException(status_code=502, detail="answer generation is temporarily unavailable") from error
        return attach_citations(answer, chunks)

    return app


app = create_app()