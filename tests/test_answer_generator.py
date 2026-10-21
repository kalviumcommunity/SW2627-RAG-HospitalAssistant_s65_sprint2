import pytest

from app.generation.answer_generator import AnswerGenerationError, AnswerGenerator


class FakeCompletions:
    def __init__(self, content: str = "Use the approved guideline.") -> None:
        self.content = content
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        message = type("Message", (), {"content": self.content})()
        choice = type("Choice", (), {"message": message})()
        return type("Response", (), {"choices": [choice]})()


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = type("Chat", (), {"completions": completions})()


def test_generator_passes_retrieved_context_to_llm() -> None:
    completions = FakeCompletions()
    answer = AnswerGenerator(client=FakeClient(completions)).generate(
        "What does the guideline say?", [{"text": "Follow the approved guideline."}]
    )
    assert answer == "Use the approved guideline."
    assert "Follow the approved guideline." in str(completions.calls[0])


def test_generator_refuses_to_answer_without_context() -> None:
    completions = FakeCompletions()
    answer = AnswerGenerator(client=FakeClient(completions)).generate("Question", [])
    assert "not contain enough information" in answer
    assert completions.calls == []


def test_generator_wraps_provider_failure() -> None:
    class BrokenCompletions:
        def create(self, **kwargs: object) -> object:
            raise RuntimeError("provider detail")

    with pytest.raises(AnswerGenerationError, match="language model request failed"):
        AnswerGenerator(client=FakeClient(BrokenCompletions())).generate("Question", [{"text": "Context"}])