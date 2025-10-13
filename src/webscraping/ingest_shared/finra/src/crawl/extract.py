from __future__ import annotations
import re
from typing import Dict, List
from bs4 import BeautifulSoup
from ..common.html_utils import clean_text, extract_links

def within_allow(url: str, allow_patterns: List[str]) -> bool:
    return any(re.compile(p).search(url) for p in allow_patterns)

def matches_deny(url: str, deny_patterns: List[str]) -> bool:
    return any(re.compile(p).search(url) for p in deny_patterns)

def extract_page_fields(html: str, url: str, selectors: Dict[str, str]) -> Dict:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.select_one(selectors.get("title", "h1")) or soup.select_one("h1"))
    title_text = clean_text(title.get_text(" ", strip=True)) if title else ""

    pub_el = soup.select_one(selectors.get("publish_date", "time[datetime]"))
    publish_date = pub_el.get("datetime") if pub_el and pub_el.has_attr("datetime") else None
    if not publish_date and pub_el:
        publish_date = clean_text(pub_el.get_text(" ", strip=True))

    breadcrumbs = [clean_text(el.get_text(" ", strip=True)) for el in soup.select(selectors.get("breadcrumbs", ".breadcrumb li"))]

    return {
        "url": url,
        "title": title_text,
        "publish_date": publish_date,
        "breadcrumbs": breadcrumbs,
        "links": extract_links(html, url),
        "html": html,
    }
