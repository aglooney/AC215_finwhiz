"""
PDF parsing helpers.
"""
import io
from typing import Optional

from pypdf import PdfReader


def extract_text_from_pdf(data: bytes) -> str:
    """
    Extract textual content from a PDF byte stream.

    For W-2 forms this usually yields structured text the LLM can consume.
    """
    buffer = io.BytesIO(data)
    reader = PdfReader(buffer)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())
    return "\n\n".join(pages)
