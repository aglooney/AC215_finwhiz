from __future__ import annotations
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, Tuple
import time

class Fetcher:
    def __init__(self, user_agent: str = "finra-rag-bot/0.1", rps: float = 1.0, timeout: float = 20.0):
        self.headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}
        self.client = httpx.Client(http2=True, headers=self.headers, timeout=timeout, follow_redirects=True)
        self._min_interval = 1.0 / max(rps, 0.1)
        self._last_time = 0.0

    def _throttle(self):
        dt = time.time() - self._last_time
        if dt < self._min_interval:
            time.sleep(self._min_interval - dt)
        self._last_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=8))
    def get(self, url: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Tuple[int, bytes, dict]:
        self._throttle()
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        r = self.client.get(url, headers=headers)
        return r.status_code, r.content, dict(r.headers)

    def close(self):
        self.client.close()
