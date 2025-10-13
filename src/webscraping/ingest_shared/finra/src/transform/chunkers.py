from __future__ import annotations
from typing import Dict, Any, List
import hashlib

def _hash_id(parts: List[str]) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]

def h2_chunker(page: Dict[str, Any], max_chars: int = 1800) -> List[Dict[str, Any]]:
    """Group content under each H2; split long groups."""
    blocks = page.get("blocks", [])
    chunks: List[Dict[str, Any]] = []
    current_title = page.get("title", "")
    h2 = None
    buf: List[str] = []

    def flush():
        nonlocal buf, h2
        if not buf:
            return
        text = "\n".join(buf).strip()
        if not text:
            buf = []
            return
        parts = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        for idx, part in enumerate(parts):
            sec = f"{h2}" if h2 else current_title
            cid = _hash_id([page.get("url", ""), sec, str(idx)])
            chunks.append({
                "id": f"{cid}",
                "source_url": page.get("url"),
                "canonical_url": page.get("url"),
                "title": current_title,
                "section": page.get("breadcrumbs", []) + ([h2] if h2 else []),
                "publish_date": page.get("publish_date"),
                "updated_date": page.get("updated_date"),
                "content": part,
                "headings_path": " > ".join(page.get("breadcrumbs", []) + ([h2] if h2 else [])),
                "type": "education",
                "tags": [],
                "compliance": {"copyright": "FINRA", "terms_hint": "educational excerpt, link required"}
            })
        buf = []

    for b in blocks:
        if b["type"] == "h2":
            flush()
            h2 = b["text"]
        elif b["type"] == "p":
            buf.append(b["text"])
        elif b["type"] == "list":
            buf.append("\n".join(f"• {it}" for it in b["items"]))
        elif b["type"] == "h3":
            buf.append(f"\n{b['text']}: ")
    flush()
    return chunks