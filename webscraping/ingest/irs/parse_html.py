"""HTML parsing helpers tailored to IRS.gov layouts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup

REMOVALS = [
    "nav",
    "footer",
    ".usa-banner",
    ".pagination",
    ".oig-banner",
    "#global-header",
    "#global-footer",
]

TARGET_TAGS = ("h1", "h2", "h3", "p", "li", "table")


@dataclass
class HtmlBlock:
    tag: str
    text: str


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_main_html(html: str) -> tuple[str, list[HtmlBlock]]:
    """Extracts relevant content blocks from a raw IRS HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main") or soup.select_one(".region-content") or soup

    for selector in REMOVALS:
        for node in main.select(selector):
            node.decompose()

    title = (soup.title.string or "").strip() if soup.title else ""
    blocks: list[HtmlBlock] = []

    for node in main.find_all(TARGET_TAGS):
        text = _clean_text(node.get_text(" ", strip=True))
        if not text:
            continue
        blocks.append(HtmlBlock(tag=node.name, text=text))

    return title, blocks


def iter_text(blocks: Iterable[HtmlBlock]) -> Iterable[str]:
    for block in blocks:
        yield block.text
