"""Defines the ingest record schema for FinWhiz documents."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class IngestRecord:
    """Normalized record for ingested financial documents.
    
    Attributes:
        id: Unique identifier for this record (format: {doc_id} or {doc_id}#p{page})
        source_url: Original URL of the document
        title: Document title
        authority: Source authority (e.g., 'consumerfinance.gov', 'irs.gov')
        doctype: Document type (e.g., 'faq', 'publication', 'webpage', 'guide')
        text: Main text content
        year: Publication or update year (if available)
        section: Section or category within the source (if applicable)
        page: Page number for multi-page documents (if applicable)
        language: ISO 639-1 language code
        ingested_at: Timestamp of when record was created
        metadata: Additional flexible metadata
    """
    id: str
    source_url: str
    title: str
    authority: str
    doctype: str
    text: str
    year: Optional[int] = None
    section: Optional[str] = None
    page: Optional[int] = None
    language: str = "en"
    ingested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, filtering out None values and empty metadata."""
        result = asdict(self)
        # Remove None values
        result = {k: v for k, v in result.items() if v is not None}
        # Remove empty metadata dict
        if not result.get("metadata"):
            result.pop("metadata", None)
        return result


def make_record(
    *,
    doc_id: str,
    url: str,
    title: str,
    authority: str,
    doctype: str,
    text: str,
    year: Optional[int] = None,
    section: Optional[str] = None,
    page: Optional[int] = None,
    language: str = "en",
    **metadata_kwargs
) -> IngestRecord:
    """Create an IngestRecord with proper ID formatting.
    
    Args:
        doc_id: Base document identifier (slugified)
        url: Source URL
        title: Document title
        authority: Source authority domain
        doctype: Type of document
        text: Main content
        year: Publication year
        section: Section/category
        page: Page number (for PDFs)
        language: Language code
        **metadata_kwargs: Additional metadata fields
    
    Returns:
        IngestRecord instance
    """
    # Format ID: use page number if available (for PDFs), otherwise just doc_id
    record_id = f"{doc_id}#p{page}" if page else doc_id
    
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
        metadata=metadata_kwargs if metadata_kwargs else {}
    )