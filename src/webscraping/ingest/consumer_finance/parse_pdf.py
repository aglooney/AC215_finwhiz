"""PDF parsing helpers using PyMuPDF."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterator

import pymupdf

LOGGER = logging.getLogger(__name__)


@dataclass
class PdfBlock:
    page: int
    text: str


def pdf_to_blocks(pdf_bytes: bytes) -> list[PdfBlock]:
    """Convert a PDF payload into page-level text blocks with error handling."""
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        LOGGER.error("Failed to open PDF: %s", exc)
        return []
    
    try:
        blocks: list[PdfBlock] = []
        for page in doc:
            try:
                text = page.get_text("text").strip()
                if not text:
                    LOGGER.debug("Empty text on page %d, skipping", page.number + 1)
                    continue
                blocks.append(PdfBlock(page=page.number + 1, text=" ".join(text.split())))
            except Exception as exc:
                LOGGER.warning("Failed to extract text from page %d: %s", page.number + 1, exc)
                continue
        
        if not blocks:
            LOGGER.warning("No text blocks extracted from PDF")
        
        return blocks
    finally:
        try:
            doc.close()
        except Exception as exc:
            LOGGER.error("Failed to close PDF document: %s", exc)


def iter_text(blocks: Iterator[PdfBlock]) -> Iterator[str]:
    for block in blocks:
        yield block.text