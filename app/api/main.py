"""Small API composition layer for retrieval, generation, and citations."""

from __future__ import annotations

import logging
import time
from uuid import uuid4
from typing import Any, Callable

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import CORS_ORIGINS, RETRIEVAL_TOP_K
from app.admin.document_indexing import (
    DocumentIndexingError,
    index_uploaded_document,
    list_indexed_documents,
    rebuild_documents,
    remove_document,
)
from app.generation.answer_generator import AnswerGenerationError, get_answer_generator
from app.generation.citations import attach_citations
from app.retrieval.service import RetrievalServiceError, retrieve_context

logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=RETRIEVAL_TOP_K, ge=1, le=10)


def create_app(
    retrieve: Callable[[str, int], list[dict[str, Any]]] = retrieve_context,
    generate: Callable[[str, list[dict[str, Any]]], str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Hospital Knowledge Assistant")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

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

    @app.get("/documents")
    def documents() -> dict[str, Any]:
        try:
            return {"documents": list_indexed_documents()}
        except (OSError, ValueError) as error:
            logger.warning("document listing failed type=%s", type(error).__name__)
            raise HTTPException(status_code=500, detail="documents could not be listed") from error

    @app.post("/documents/upload")
    def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
        try:
            content = file.file.read()
            return index_uploaded_document(content, file.filename or "")
        except DocumentIndexingError as error:
            logger.warning("document upload failed type=%s", type(error).__name__)
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            file.file.close()

    @app.delete("/documents/{document_name}")
    def delete_document(document_name: str) -> dict[str, Any]:
        try:
            return remove_document(document_name)
        except DocumentIndexingError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/documents/rebuild")
    def rebuild_document_index() -> dict[str, Any]:
        try:
            return rebuild_documents()
        except Exception as error:
            logger.exception("document rebuild failed")
            raise HTTPException(status_code=500, detail="document rebuild failed") from error

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
                answer = get_answer_generator().generate(request.question, chunks)
        except AnswerGenerationError as error:
            logger.warning("answer generation failed type=%s", type(error).__name__)
            raise HTTPException(status_code=502, detail="answer generation is temporarily unavailable") from error
        return attach_citations(answer, chunks)

    return app


app = create_app()