from pathlib import Path

from app.loaders.document_loader import DocumentPage
from scripts.index_documents import index_documents


class FakeEmbedder:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]


def test_indexing_connects_processing_and_storage(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "Protocol.pdf"
    source.write_bytes(b"placeholder")
    page = DocumentPage("protocol", source.name, str(source), 1, "Emergency response protocol " * 20)
    monkeypatch.setattr("scripts.index_documents.load_pdf", lambda _: [page])

    stats = index_documents(tmp_path, tmp_path / "vectors.json", FakeEmbedder(), 40, 5)

    assert stats["documents"] == 1
    assert stats["chunks"] > 1
    assert stats["indexed_vectors"] == stats["chunks"]
    assert stats["failed_documents"] == []