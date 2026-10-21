"""Generate bounded answers from caller-provided retrieval context."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.config import LLM_API_KEY, LLM_MODEL, LLM_PROVIDER


class AnswerGenerationError(RuntimeError):
    """Raised when the configured language model cannot answer."""


class AnswerGenerator:
    """Small provider adapter that never performs retrieval itself."""

    def __init__(
        self,
        model: str = LLM_MODEL,
        provider: str = LLM_PROVIDER,
        api_key: str | None = LLM_API_KEY,
        client: Any | None = None,
    ) -> None:
        if provider != "openai":
            raise ValueError(f"unsupported LLM provider: {provider}")
        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def generate(self, question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
        """Generate an answer only when the caller supplied relevant context."""
        if not question.strip():
            raise ValueError("question must not be empty")
        if not retrieved_chunks:
            return "The supplied documents do not contain enough information to answer this question."

        context = "\n\n".join(str(chunk.get("text", "")).strip() for chunk in retrieved_chunks)
        if not context.strip():
            return "The supplied documents do not contain enough information to answer this question."
        prompt = (
            "Answer only from the supplied document context. Do not invent facts or provide "
            "patient-specific medical advice. If the context is insufficient, say so clearly.\n\n"
            f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION:\n{question}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cautious educational hospital knowledge assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            answer = response.choices[0].message.content
        except Exception as error:
            raise AnswerGenerationError("language model request failed") from error
        if not answer or not answer.strip():
            raise AnswerGenerationError("language model returned an empty answer")
        return answer.strip()