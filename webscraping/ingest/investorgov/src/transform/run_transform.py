import argparse
from pathlib import Path
import yaml
import re
from bs4 import BeautifulSoup
import json

def extract_text(html_content, selectors_cfg):
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove excluded selectors
    for sel in selectors_cfg.get("exclude", []):
        for el in soup.select(sel):
            el.decompose()

    # Try primary text selectors
    parts = []
    for sel in selectors_cfg.get("text", []):
        for el in soup.select(sel):
            text = el.get_text(strip=True)
            if text:
                parts.append(text)

    # Fallback to <body> if nothing found
    if not parts:
        body = soup.find("body")
        if body:
            text = body.get_text(" ", strip=True)
            if text:
                parts.append(text)

    return "\n".join(parts)

def transform_one(html_path, selectors_cfg, routing_cfg, out_chunk_dir):
    content = html_path.read_text(encoding="utf-8", errors="ignore")
    body = extract_text(content, selectors_cfg)
    if not body.strip():
        return None

    fname = html_path.stem
    route_tags = []

    original_url = html_path.stem.replace("_", "/").replace("https", "https:")
    for route in routing_cfg.get("routes", []):
        if re.match(route["match"], original_url):
            route_tags = route.get("tags", [])
            break

    chunk = {
        "id": f"investor-{fname}",
        "source": html_path.name,
        "title": fname,
        "content": body,
        "tags": route_tags
    }

    out_file = out_chunk_dir / f"{fname}.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(chunk) + "\n")
    return out_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="indir", required=True)
    parser.add_argument("--out", dest="outdir", required=True)
    parser.add_argument("--selectors", required=True)
    parser.add_argument("--routing", required=True)
    args = parser.parse_args()

    sel_cfg = yaml.safe_load(open(args.selectors))
    routing_cfg = yaml.safe_load(open(args.routing))
    in_dir = Path(args.indir)
    out_dir = Path(args.outdir) / "chunks"
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    success = 0
    for html_file in in_dir.glob("*.html"):
        total += 1
        result = transform_one(html_file, sel_cfg, routing_cfg, out_dir)
        if result:
            success += 1
            print(f"✅ Transformed {html_file.name}")
        else:
            print(f"⚠️ Skipped {html_file.name} (no content)")

    print(f"\nDone. {success}/{total} pages transformed successfully.")

if __name__ == "__main__":
    main()