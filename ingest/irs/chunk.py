"""Chunking logic to produce retrieval-friendly segments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class Chunk:
    text: str
    section: Optional[str]
    start_page: Optional[int] = None


def chunk_blocks(blocks: Iterable[dict], max_chars: int = 1200) -> list[Chunk]:
    """Aggregate sequential blocks into approximately max_chars chunks."""
    chunks: list[Chunk] = []
    buffer: list[dict] = []
    buffer_len = 0
    current_section: Optional[str] = None

    for block in blocks:
        text = block.get("text", "").strip()
        if not text:
            continue

        tag = block.get("tag", "")
        if tag and tag.lower().startswith("h"):
            current_section = text

        if buffer and buffer_len + len(text) > max_chars:
            chunks.append(_buffer_to_chunk(buffer))
            buffer = []
            buffer_len = 0

        buffer.append({
            "text": text,
            "section": block.get("section") or current_section,
            "page": block.get("page"),
        })
        buffer_len += len(text) + 1

    if buffer:
        chunks.append(_buffer_to_chunk(buffer))

    return chunks


def _buffer_to_chunk(buffer: list[dict]) -> Chunk:
    text = "\n".join(item["text"] for item in buffer)
    section = buffer[0].get("section")
    pages = [item.get("page") for item in buffer if item.get("page") is not None]
    start_page = pages[0] if pages else None
    return Chunk(text=text, section=section, start_page=start_page)
