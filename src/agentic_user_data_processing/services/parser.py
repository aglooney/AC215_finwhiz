"""
PDF parsing and form extraction router.
Handles both W-2 and 1099-INT forms.
"""
import io
from typing import Optional
from pypdf import PdfReader

from . import extraction, extraction_1099


# ---------------------------------------------------------------------
# Text Extraction
# ---------------------------------------------------------------------
def extract_text_from_pdf(data: bytes) -> str:
    """
    Extract textual content from a PDF byte stream.
    This is the first step before passing text to the LLM extractor.
    """
    buffer = io.BytesIO(data)
    reader = PdfReader(buffer)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())
    return "\n\n".join(pages)


# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------
async def extract_fields(document_text: str, form_type: str):
    """
    Dynamically route to the correct form extraction logic.
    - W-2 → extraction.extract_w2_fields
    - 1099-INT → extraction_1099.extract_1099_fields
    """
    form_type = form_type.strip().lower()

    if form_type == "w2":
        return await extraction.extract_w2_fields(document_text)
    elif form_type in ["1099", "1099-int"]:
        return await extraction_1099.extract_1099_fields(document_text)
    else:
        raise ValueError(f"Unsupported form type: {form_type}")
