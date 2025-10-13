"""Defines the ingest record schema for FinWhiz IRS documents."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class IngestRecord:
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
        return asdict(self)


def make_record(*, doc_id: str, url: str, title: str, year: Optional[int],
                section: Optional[str], chunk_id: int, text: str,
                authority: str = "irs.gov", doctype: str = "publication",
                language: str = "en", page: Optional[int] = None) -> IngestRecord:
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
