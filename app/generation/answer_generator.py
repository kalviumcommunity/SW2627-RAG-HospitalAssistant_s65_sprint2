"""Generate bounded answers from caller-provided retrieval context."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.config import LLM_API_KEY, LLM_MODEL, LLM_PROVIDER
from app.generation.prompt_builder import INSUFFICIENT_CONTEXT, build_grounded_prompt


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
            return INSUFFICIENT_CONTEXT
        prompt = build_grounded_prompt(question, retrieved_chunks)
        if prompt == INSUFFICIENT_CONTEXT:
            return prompt
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