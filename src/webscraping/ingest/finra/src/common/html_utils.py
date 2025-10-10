from __future__ import annotations
from bs4 import BeautifulSoup
import re
from typing import List, Dict

_WS = re.compile(r"\s+")

def clean_text(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = _WS.sub(" ", s)
    return s.strip()

def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    out: List[str] = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href or href.startswith("#"):
            continue
        if href.startswith(("http://", "https://")):
            out.append(href)
        elif href.startswith("/"):
            from urllib.parse import urljoin
            out.append(urljoin(base_url, href))
    # dedupe, preserve order
    return list(dict.fromkeys(out))

def select_texts(html: str, selectors: Dict[str, str]) -> Dict[str, List[str]]:
    soup = BeautifulSoup(html, "lxml")
    out: Dict[str, List[str]] = {}
    for key, css in selectors.items():
        out[key] = [clean_text(el.get_text(" ", strip=True)) for el in soup.select(css)]
    return out
