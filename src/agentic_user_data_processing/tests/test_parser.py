import pytest
from pathlib import Path
from agentic_user_data_processing.services import parser


ROOT_DIR = Path(__file__).resolve().parents[3]


def test_extract_text_from_pdf_with_sample():
    pdf_path = ROOT_DIR / "src" / "synthetic_data" / "w2" / "outputs" / "w2_000.pdf"
    if not pdf_path.exists():
        pytest.skip("Sample PDF not found")

    pdf_bytes = pdf_path.read_bytes()
    text = parser.extract_text_from_pdf(pdf_bytes)

    assert isinstance(text, str)
    assert len(text) > 0


def test_extract_text_from_pdf_empty_bytes():
    # Should handle empty/invalid PDF gracefully
    with pytest.raises(Exception):
        parser.extract_text_from_pdf(b"")


def test_extract_text_from_pdf_invalid_pdf():
    # Should handle invalid PDF content
    with pytest.raises(Exception):
        parser.extract_text_from_pdf(b"not a pdf content")
