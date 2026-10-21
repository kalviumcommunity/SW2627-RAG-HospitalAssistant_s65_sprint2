from app.loaders.document_loader import DocumentPage
from app.processing.text_cleaner import clean_page, clean_text


def test_clean_text_normalizes_whitespace_and_blank_lines() -> None:
    assert clean_text("  Blood   pressure\n\n\n  monitor  ") == "Blood pressure\n\nmonitor"


def test_clean_text_handles_empty_text() -> None:
    assert clean_text("") == ""


def test_clean_text_preserves_medical_terms() -> None:
    text = "Administer acetaminophen 500 mg; monitor SpO2."
    assert clean_text(text) == text


def test_clean_page_preserves_source_metadata() -> None:
    page = DocumentPage("protocol", "Protocol.pdf", "/tmp/Protocol.pdf", 3, "  dose  \n")

    cleaned = clean_page(page)

    assert cleaned.text == "dose"
    assert cleaned.document_id == page.document_id
    assert cleaned.document_name == page.document_name
    assert cleaned.source_path == page.source_path
    assert cleaned.page_number == page.page_number