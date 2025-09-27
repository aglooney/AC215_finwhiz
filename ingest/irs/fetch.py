"""Utilities for fetching IRS content over HTTP."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import requests

DEFAULT_HEADERS = {"User-Agent": "FW-Ingest/0.1"}


@dataclass
class FetchResult:
    """Represents an HTTP payload fetched from a source URL."""

    url: str
    content: str | bytes
    content_type: str

    @property
    def is_html(self) -> bool:
        return "text/html" in self.content_type

    @property
    def is_pdf(self) -> bool:
        return "application/pdf" in self.content_type or self.url.lower().endswith(".pdf")


def fetch_url(url: str, *, headers: Optional[dict[str, str]] = None, sleep: float = 0.5,
              session: Optional[requests.Session] = None) -> FetchResult:
    """Fetches a URL and returns the raw payload with content metadata."""
    sess = session or requests.Session()
    response = sess.get(url, headers=headers or DEFAULT_HEADERS, timeout=30)
    time.sleep(max(sleep, 0))
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    is_html = "text/html" in content_type
    payload: str | bytes
    if is_html:
        payload = response.text
    else:
        payload = response.content
    return FetchResult(url=url, content=payload, content_type=content_type)


def resolve_url(base_url: str, href: str) -> str:
    """Resolve relative links using the originating URL as the base."""
    return urljoin(base_url, href)
