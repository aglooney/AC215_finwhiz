"""Generic HTML parsing helpers for government financial sites."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup

# Common elements to remove from most government sites
DEFAULT_REMOVALS = [
    "nav",
    "footer",
    "header",
    ".usa-banner",
    ".pagination",
    ".breadcrumb",
    ".social-share",
    ".oig-banner",
    "#global-header",
    "#global-footer",
]

TARGET_TAGS = ("h1", "h2", "h3", "h4", "p", "li", "table", "blockquote")


@dataclass
class HtmlBlock:
    tag: str
    text: str


def _clean_text(text: str) -> str:
    """Normalize whitespace in text."""
    return " ".join(text.split())


def extract_main_html(html: str, *, additional_removals: list[str] | None = None) -> tuple[str, list[HtmlBlock]]:
    """
    Extract relevant content blocks from HTML.
    
    Args:
        html: Raw HTML string
        additional_removals: Extra CSS selectors to remove (source-specific)
    
    Returns:
        Tuple of (title, blocks)
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Try to find main content area (different sites use different selectors)
    main = (
        soup.select_one("main") or 
        soup.select_one(".region-content") or 
        soup.select_one("#content") or 
        soup.select_one("article") or
        soup
    )

    # Remove navigation, ads, etc.
    removals = DEFAULT_REMOVALS + (additional_removals or [])
    for selector in removals:
        for node in main.select(selector):
            node.decompose()

    # Extract title
    title = (soup.title.string or "").strip() if soup.title else ""
    
    # Extract content blocks
    blocks: list[HtmlBlock] = []
    for node in main.find_all(TARGET_TAGS):
        text = _clean_text(node.get_text(" ", strip=True))
        if not text:
            continue
        blocks.append(HtmlBlock(tag=node.name, text=text))

    return title, blocks


def iter_text(blocks: Iterable[HtmlBlock]) -> Iterable[str]:
    """Iterate over just the text content of blocks."""
    for block in blocks:
        yield block.text