"""Small API composition layer for retrieval, generation, and citations."""

from __future__ import annotations

import logging
import time
from uuid import uuid4
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.generation.answer_generator import AnswerGenerationError, AnswerGenerator
from app.generation.citations import attach_citations
from app.retrieval.service import RetrievalServiceError, retrieve_context

logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


def create_app(
    retrieve: Callable[[str, int], list[dict[str, Any]]] = retrieve_context,
    generate: Callable[[str, list[dict[str, Any]]], str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Hospital Knowledge Assistant")

    @app.middleware("http")
    async def request_context(request: Request, call_next: Any) -> Any:
        supplied_request_id = request.headers.get("X-Request-ID", "").strip()
        request_id = supplied_request_id if 0 < len(supplied_request_id) <= 128 else uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled request failure id=%s path=%s", request_id, request.url.path)
            response = JSONResponse(
                status_code=500,
                content={"detail": "internal server error"},
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        logger.info("request completed id=%s path=%s status=%s duration_ms=%.1f", request_id, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask")
    def ask(request: AskRequest) -> dict[str, Any]:
        try:
            chunks = retrieve(request.question, request.top_k)
        except RetrievalServiceError as error:
            logger.warning("retrieval failed type=%s", type(error).__name__)
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
            logger.warning("answer generation failed type=%s", type(error).__name__)
            raise HTTPException(status_code=502, detail="answer generation is temporarily unavailable") from error
        return attach_citations(answer, chunks)

    return app


app = create_app()