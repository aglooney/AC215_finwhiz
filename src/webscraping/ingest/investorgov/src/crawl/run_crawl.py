import argparse
import yaml
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re

def load_allowlist(path):
    with open(path) as f:
        return yaml.safe_load(f)

def should_follow(url, allow_regexes, deny_regexes):
    for dr in deny_regexes:
        if re.match(dr, url):
            return False
    for ar in allow_regexes:
        if re.match(ar, url):
            return True
    return False

def crawl_seed(seed_url, allow, deny, visited, out_dir):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/"
            }
        r = requests.get(seed_url, timeout=10, headers=headers)
        r.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {seed_url}: {e}")
        return

    html = r.text
    filename = seed_url.replace("/", "_").replace(":", "")
    (out_dir / (filename + ".html")).write_text(html, encoding="utf-8")
    visited.add(seed_url)

    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Normalize absolute/relative
        if href.startswith("/"):
            href = "https://www.investor.gov" + href
        if href.startswith("http"):
            if href not in visited and should_follow(href, allow, deny):
                crawl_seed(href, allow, deny, visited, out_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = load_allowlist(args.seeds)
    seeds = config.get("seeds", [])
    allow = config.get("allow", [])
    deny = config.get("deny", [])

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    visited = set()
    for s in seeds:
        crawl_seed(s, allow, deny, visited, out_dir)

if __name__ == "__main__":
    main()