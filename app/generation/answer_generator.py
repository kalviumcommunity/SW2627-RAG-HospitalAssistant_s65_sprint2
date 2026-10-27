"""Generate bounded answers from caller-provided retrieval context."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from app.config import LLM_API_KEY, LLM_MAX_OUTPUT_TOKENS, LLM_MODEL, LLM_PROVIDER, LLM_TIMEOUT_MS
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
        if provider != "gemini":
            raise ValueError(f"unsupported LLM provider: {provider}")
        if client is None and not api_key:
            raise ValueError("GEMINI_API_KEY must be configured")
        self.model = model
        self.client = client or genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
        )

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
            response = self.client.models.generate_content(
                model=self.model,
                contents=(
                    "You are a cautious educational hospital knowledge assistant. "
                    "Answer only from the supplied context.\n\n" + prompt
                ),
                config={"max_output_tokens": LLM_MAX_OUTPUT_TOKENS},
            )
            answer = response.text if response is not None else None
        except Exception as error:
            raise AnswerGenerationError("language model request failed") from error
        if not answer or not answer.strip():
            raise AnswerGenerationError("language model returned an empty answer")
        return answer.strip()


@lru_cache(maxsize=1)
def get_answer_generator() -> AnswerGenerator:
    """Reuse the Gemini client across requests."""
    return AnswerGenerator()