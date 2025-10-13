"""HTML parsing helpers tailored to consumerfinance.gov layouts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup

# Consumer Finance specific removals (more than IRS default)
DEFAULT_REMOVALS = [
    "nav",
    "footer",
    ".usa-banner",
    ".pagination",
    ".breadcrumb",
    ".social-share",
    ".o-email-signup",
    ".m-notification",
    "#global-header",
    "#global-footer",
]

# Standard content tags
DEFAULT_TARGET_TAGS = ("h1", "h2", "h3", "h4", "p", "li", "table")


@dataclass
class HtmlBlock:
    tag: str
    text: str


def _clean_text(text: str) -> str:
    """Normalize whitespace in text."""
    return " ".join(text.split())


def extract_main_html(
    html: str,
    *,
    removals: list[str] | None = None,
    target_tags: tuple[str, ...] | None = None,
    main_selector: str | None = None,
) -> tuple[str, list[HtmlBlock]]:
    """Extracts relevant content blocks from a consumer finance HTML page.
    
    Args:
        html: Raw HTML string
        removals: CSS selectors to remove (uses DEFAULT_REMOVALS if None)
        target_tags: Tags to extract (uses DEFAULT_TARGET_TAGS if None)
        main_selector: CSS selector for main content area
        
    Returns:
        Tuple of (title, list of HtmlBlock objects)
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Find main content area
    if main_selector:
        main = soup.select_one(main_selector) or soup
    else:
        main = soup.select_one("main") or soup.select_one(".region-content") or soup

    # Remove unwanted elements
    for selector in removals or DEFAULT_REMOVALS:
        for node in main.select(selector):
            node.decompose()

    # Extract title
    title = (soup.title.string or "").strip() if soup.title else ""
    
    # Extract content blocks
    blocks: list[HtmlBlock] = []
    for node in main.find_all(target_tags or DEFAULT_TARGET_TAGS):
        text = _clean_text(node.get_text(" ", strip=True))
        if not text:
            continue
        blocks.append(HtmlBlock(tag=node.name, text=text))

    return title, blocks


def iter_text(blocks: Iterable[HtmlBlock]) -> Iterable[str]:
    """Yield text from HtmlBlock objects.
    
    Args:
        blocks: Iterable of HtmlBlock objects
        
    Yields:
        Text content from each block
    """
    for block in blocks:
        yield block.text