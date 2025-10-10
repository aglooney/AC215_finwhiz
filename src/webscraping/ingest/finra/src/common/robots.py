from __future__ import annotations
from urllib.parse import urlparse
import urllib.robotparser as robotparser
from functools import lru_cache

@lru_cache(maxsize=64)
def _rp_for(netloc: str) -> robotparser.RobotFileParser:
    rp = robotparser.RobotFileParser()
    rp.set_url(f"https://{netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        pass
    return rp

def allowed(url: str, user_agent: str) -> bool:
    netloc = urlparse(url).netloc
    rp = _rp_for(netloc)
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return False