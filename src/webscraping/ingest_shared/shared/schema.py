"""Defines the ingest record schema for document ingestion."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class IngestRecord:
    """Standard record format for ingested documents."""
    
    id: str
    source_url: str
    title: str
    year: Optional[int]
    section: Optional[str]
    authority: str
    doctype: str
    language: str
    text: str
    page: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return asdict(self)


def make_record(
    *,
    doc_id: str,
    url: str,
    title: str,
    year: Optional[int],
    section: Optional[str],
    chunk_id: int,
    text: str,
    authority: str = "unknown",
    doctype: str = "document",
    language: str = "en",
    page: Optional[int] = None,
) -> IngestRecord:
    """Factory function to create an IngestRecord.
    
    Args:
        doc_id: Document identifier (slug)
        url: Source URL
        title: Document title
        year: Year associated with the document
        section: Section heading (if applicable)
        chunk_id: Chunk number within the document
        text: The actual text content
        authority: Source authority (e.g., 'irs.gov', 'finra.org')
        doctype: Document type (e.g., 'publication', 'webpage')
        language: Language code (default 'en')
        page: Page number (for PDFs)
        
    Returns:
        IngestRecord instance
    """
    record_id = f"{doc_id}#c{chunk_id}"
    return IngestRecord(
        id=record_id,
        source_url=url,
        title=title,
        year=year,
        section=section,
        authority=authority,
        doctype=doctype,
        language=language,
        text=text,
        page=page,
    )