from __future__ import annotations
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from ..common.html_utils import clean_text

def html_to_blocks(html: str) -> List[Dict[str, Any]]:
    """Create a sequence of blocks preserving H2/H3 structure and paragraphs/lists."""
    soup = BeautifulSoup(html, "lxml")
    article = soup.select_one("main article") or soup
    blocks: List[Dict[str, Any]] = []
    for el in article.find_all(["h2", "h3", "p", "ul", "ol"], recursive=True):
        if el.name == "p":
            text = clean_text(el.get_text(" ", strip=True))
            if text:
                blocks.append({"type": "p", "text": text})
        elif el.name in ("ul", "ol"):
            items = [clean_text(li.get_text(" ", strip=True)) for li in el.find_all("li", recursive=False)]
            items = [x for x in items if x]
            if items:
                blocks.append({"type": "list", "items": items})
        else:  # h2/h3
            text = clean_text(el.get_text(" ", strip=True))
            lvl = 2 if el.name == "h2" else 3
            blocks.append({"type": f"h{lvl}", "text": text})
    return blocks
