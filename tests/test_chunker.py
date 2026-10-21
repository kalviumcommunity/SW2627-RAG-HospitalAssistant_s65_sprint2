from app.loaders.document_loader import DocumentPage
from app.processing.chunker import chunk_page


def test_chunk_page_splits_and_preserves_metadata() -> None:
    page = DocumentPage("protocol", "Protocol.pdf", "raw/Protocol.pdf", 2, "abcdefghij")

    chunks = chunk_page(page, chunk_size=6, chunk_overlap=2)

    assert [chunk["text"] for chunk in chunks] == ["abcdef", "efghij", "ij"]
    assert chunks[0]["document_name"] == "Protocol.pdf"
    assert chunks[0]["page_number"] == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["chunk_id"] != chunks[1]["chunk_id"]


def test_empty_page_produces_no_chunks() -> None:
    page = DocumentPage("empty", "Empty.pdf", "raw/Empty.pdf", 1, "   ")
    assert chunk_page(page) == []


def test_chunk_settings_are_validated() -> None:
    page = DocumentPage("protocol", "Protocol.pdf", "raw/Protocol.pdf", 1, "text")
    for size, overlap in [(0, 0), (5, 5), (5, 6), (5, -1)]:
        try:
            chunk_page(page, size, overlap)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid chunk settings should fail")