"""Utilities for fetching content over HTTP."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import requests

DEFAULT_HEADERS = {"User-Agent": "FW-Ingest/0.1"}
LOGGER = logging.getLogger(__name__)


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
              session: Optional[requests.Session] = None, retries: int = 3) -> FetchResult:
    """Fetches a URL with retry logic and returns the raw payload with content metadata."""
    sess = session or requests.Session()
    
    for attempt in range(retries):
        try:
            response = sess.get(url, headers=headers or DEFAULT_HEADERS, timeout=30)
            response.raise_for_status()
            time.sleep(max(sleep, 0))
            
            content_type = response.headers.get("content-type", "")
            is_html = "text/html" in content_type
            payload: str | bytes
            if is_html:
                payload = response.text
            else:
                payload = response.content
            
            return FetchResult(url=url, content=payload, content_type=content_type)
            
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                LOGGER.error("Timeout fetching %s after %d attempts", url, retries)
                raise
            wait_time = 2 ** attempt
            LOGGER.warning("Timeout on attempt %d for %s, retrying in %ds", attempt + 1, url, wait_time)
            time.sleep(wait_time)
            
        except requests.exceptions.RequestException as exc:
            if attempt == retries - 1:
                LOGGER.error("Failed to fetch %s after %d attempts: %s", url, retries, exc)
                raise
            wait_time = 2 ** attempt
            LOGGER.warning("Error on attempt %d for %s: %s, retrying in %ds", attempt + 1, url, exc, wait_time)
            time.sleep(wait_time)
    
    # Should never reach here due to raises above, but for type checking
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def resolve_url(base_url: str, href: str) -> str:
    """Resolve relative links using the originating URL as the base."""
    return urljoin(base_url, href)