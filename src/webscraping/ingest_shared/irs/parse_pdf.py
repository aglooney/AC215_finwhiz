"""PDF parsing helpers using PyMuPDF."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pymupdf


@dataclass
class PdfBlock:
    page: int
    text: str


def pdf_to_blocks(pdf_bytes: bytes) -> list[PdfBlock]:
    """Convert a PDF payload into page-level text blocks."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        blocks: list[PdfBlock] = []
        for page in doc:
            text = page.get_text("text").strip()
            if not text:
                continue
            blocks.append(PdfBlock(page=page.number + 1, text=" ".join(text.split())))
        return blocks
    finally:
        doc.close()


def iter_text(blocks: Iterator[PdfBlock]) -> Iterator[str]:
    for block in blocks:
        yield block.text
