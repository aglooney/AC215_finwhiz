"""Tests for parser module."""

from unittest.mock import patch, MagicMock


def test_extract_text_from_pdf_valid():
    """Test extraction with valid PDF bytes."""
    with (
        patch("agentic_user_data_processing.services.parser.Path") as mock_path,
        patch("agentic_user_data_processing.services.parser.subprocess.run") as mock_subprocess,
        patch("agentic_user_data_processing.services.parser.PdfReader") as mock_reader,
        patch("agentic_user_data_processing.services.parser.pdfminer_extract_text") as mock_pdfminer,
    ):

        # Setup path mock
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.with_name.return_value = mock_path_instance

        # Setup subprocess mock (ghostscript)
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Setup PdfReader mock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content from PDF"
        mock_reader.return_value.__enter__ = MagicMock(return_value=mock_reader.return_value)
        mock_reader.return_value.__exit__ = MagicMock(return_value=False)
        mock_reader.return_value.pages = [mock_page]

        # Setup pdfminer mock
        mock_pdfminer.return_value = "Test content from pdfminer"

        from agentic_user_data_processing.services import parser

        result = parser.extract_text_from_pdf(b"%PDF-1.4 test content")

        assert isinstance(result, str)


def test_extract_text_from_pdf_ghostscript_not_found():
    """Test fallback when Ghostscript is not installed."""
    with (
        patch("agentic_user_data_processing.services.parser.Path") as mock_path,
        patch("agentic_user_data_processing.services.parser.subprocess.run") as mock_subprocess,
        patch("agentic_user_data_processing.services.parser.PdfReader") as mock_reader,
        patch("agentic_user_data_processing.services.parser.pdfminer_extract_text") as mock_pdfminer,
    ):

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.with_name.return_value = mock_path_instance

        # Simulate Ghostscript not found
        mock_subprocess.side_effect = FileNotFoundError()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Fallback content"
        mock_reader.return_value.pages = [mock_page]
        mock_pdfminer.return_value = "Pdfminer fallback"

        from agentic_user_data_processing.services import parser

        result = parser.extract_text_from_pdf(b"%PDF-1.4 test")

        assert isinstance(result, str)


def test_extract_text_from_pdf_pypdf_failure():
    """Test fallback to pdfminer when PyPDF fails."""
    with (
        patch("agentic_user_data_processing.services.parser.Path") as mock_path,
        patch("agentic_user_data_processing.services.parser.subprocess.run") as mock_subprocess,
        patch("agentic_user_data_processing.services.parser.PdfReader") as mock_reader,
        patch("agentic_user_data_processing.services.parser.pdfminer_extract_text") as mock_pdfminer,
    ):

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.with_name.return_value = mock_path_instance

        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_reader.side_effect = Exception("PyPDF failed")
        mock_pdfminer.return_value = "Pdfminer extracted text"

        from agentic_user_data_processing.services import parser

        result = parser.extract_text_from_pdf(b"%PDF-1.4 test")

        assert "Pdfminer extracted text" in result


def test_extract_text_cleans_cid_artifacts():
    """Test that CID artifacts are cleaned from output."""
    with (
        patch("agentic_user_data_processing.services.parser.Path") as mock_path,
        patch("agentic_user_data_processing.services.parser.subprocess.run") as mock_subprocess,
        patch("agentic_user_data_processing.services.parser.PdfReader") as mock_reader,
        patch("agentic_user_data_processing.services.parser.pdfminer_extract_text") as mock_pdfminer,
    ):

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.with_name.return_value = mock_path_instance

        mock_subprocess.return_value = MagicMock(returncode=0)

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Text (cid:123) with (cid:456) artifacts"
        mock_reader.return_value.pages = [mock_page]
        mock_pdfminer.return_value = ""

        from agentic_user_data_processing.services import parser

        result = parser.extract_text_from_pdf(b"%PDF-1.4 test")

        assert "(cid:" not in result
