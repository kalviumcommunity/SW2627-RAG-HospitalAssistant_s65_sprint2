import pytest

from app.generation.answer_generator import AnswerGenerationError, AnswerGenerator


class FakeModels:
    def __init__(self, content: str = "Use the approved guideline.") -> None:
        self.content = content
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return type("Response", (), {"text": self.content})()


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


def test_generator_passes_retrieved_context_to_llm() -> None:
    models = FakeModels()
    answer = AnswerGenerator(client=FakeClient(models)).generate(
        "What does the guideline say?", [{"text": "Follow the approved guideline."}]
    )
    assert answer == "Use the approved guideline."
    assert "Follow the approved guideline." in str(models.calls[0])


def test_generator_refuses_to_answer_without_context() -> None:
    models = FakeModels()
    answer = AnswerGenerator(client=FakeClient(models)).generate("Question", [])
    assert "not contain enough information" in answer
    assert models.calls == []


def test_generator_wraps_provider_failure() -> None:
    class BrokenModels:
        def generate_content(self, **kwargs: object) -> object:
            raise RuntimeError("provider detail")

    with pytest.raises(AnswerGenerationError, match="language model request failed"):
        AnswerGenerator(client=FakeClient(BrokenModels())).generate("Question", [{"text": "Context"}])