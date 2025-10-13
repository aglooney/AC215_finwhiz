"""PDF parsing helpers using PyMuPDF."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pymupdf


@dataclass
class PdfBlock:
    """Represents a block of text extracted from a PDF page."""
    
    page: int
    text: str


def pdf_to_blocks(pdf_bytes: bytes) -> list[PdfBlock]:
    """Convert a PDF payload into page-level text blocks.
    
    Args:
        pdf_bytes: Raw PDF file content as bytes
        
    Returns:
        List of PdfBlock objects, one per non-empty page
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        blocks: list[PdfBlock] = []
        for page in doc:
            text = page.get_text("text").strip()
            if not text:
                continue
            # Normalize whitespace
            text = " ".join(text.split())
            blocks.append(PdfBlock(page=page.number + 1, text=text))
        return blocks
    finally:
        doc.close()


def iter_text(blocks: Iterator[PdfBlock]) -> Iterator[str]:
    """Yield text from PdfBlock objects.
    
    Args:
        blocks: Iterator of PdfBlock objects
        
    Yields:
        Text content from each block
    """
    for block in blocks:
        yield block.text