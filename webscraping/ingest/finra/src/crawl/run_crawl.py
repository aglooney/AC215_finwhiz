from __future__ import annotations
import os
from pathlib import Path
import re
import time
import yaml
import typer
from typing import List
from ..common.io_utils import ensure_dir, sha256_of_bytes, write_gzip_bytes, write_json_gz
from ..common.robots import allowed
from .frontier import Frontier
from .fetch import Fetcher
from .extract import extract_page_fields, within_allow, matches_deny

app = typer.Typer(add_completion=False)

def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@app.command()
def main(
    seeds: str = typer.Option(..., help="Path to crawl_allowlist.yml"),
    blocklist: str = typer.Option("config/crawl_blocklist.yml", help="Path to crawl_blocklist.yml"),
    selectors_path: str = typer.Option("config/selectors.yml", help="CSS selectors config"),
    out: str = typer.Option("data/raw_html", help="Output dir for raw html"),
    parsed_out: str = typer.Option("data/parsed_json", help="Output dir for parsed json"),
    max_pages: int = typer.Option(200, help="Max pages to fetch"),
    rps: float = typer.Option(float(os.getenv("RPS", "1.0")), help="Requests per second"),
    user_agent: str = typer.Option(os.getenv("HTTP_USER_AGENT", "finra-rag-bot/0.1")),
):
    seeds_cfg = load_yaml(seeds)
    allow_patterns: List[str] = seeds_cfg.get("allow", [])
    seed_urls: List[str] = seeds_cfg.get("seeds", [])

    deny_patterns: List[str] = load_yaml(blocklist).get("deny", [])
    selectors = load_yaml(selectors_path)

    ensure_dir(out)
    ensure_dir(parsed_out)

    fetcher = Fetcher(user_agent=user_agent, rps=rps)
    fr = Frontier(seed_urls)

    fetched = 0
    start = time.time()

    try:
        while fetched < max_pages and len(fr) > 0:
            url = fr.pop()
            if not url:
                break
            if not within_allow(url, allow_patterns):
                continue
            if matches_deny(url, deny_patterns):
                continue
            if not allowed(url, user_agent):
                continue

            status, content, headers = fetcher.get(url)
            if status in (304, 204) or status >= 400:
                continue

            sha = sha256_of_bytes(content)
            day = time.strftime("%Y/%m/%d")
            raw_path = Path(out) / day / f"{sha}.html.gz"
            write_gzip_bytes(raw_path, content)

            page = extract_page_fields(content.decode("utf-8", errors="ignore"), url, selectors)
            write_json_gz(Path(parsed_out) / f"{sha}.json.gz", page)

            for link in page["links"]:
                if matches_deny(link, deny_patterns):
                    continue
                if not within_allow(link, allow_patterns):
                    continue
                if allowed(link, user_agent):
                    fr.push(link)

            fetched += 1
    finally:
        fetcher.close()

    dur = time.time() - start
    print(f"Fetched {fetched} pages in {dur:.1f}s → {out}")

if __name__ == "__main__":
    app()
