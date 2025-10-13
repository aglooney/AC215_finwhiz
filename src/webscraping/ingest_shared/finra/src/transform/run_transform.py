from __future__ import annotations
from pathlib import Path
import typer
import yaml
from ..common.io_utils import iter_paths, read_json_gz, write_json_gz, ensure_dir
from .normalize import html_to_blocks
from .chunkers import h2_chunker

app = typer.Typer(add_completion=False)

@app.command()
def main(
    _in: str = typer.Option("data/raw_html", "--in", help="Dir of raw_html (unused; we read parsed_json)"),
    out: str = typer.Option("data", help="Base output dir (parsed_json, chunks)"),
    selectors: str = typer.Option("config/selectors.yml"),
    routing: str = typer.Option("config/routing.yml"),
):
    parsed_dir = Path(out) / "parsed_json"
    chunks_dir = Path(out) / "chunks"
    ensure_dir(chunks_dir)

    _ = yaml.safe_load(open(routing, "r", encoding="utf-8"))  # reserved for future routing
    count = 0
    for p in iter_paths(parsed_dir, ".json.gz"):
        page = read_json_gz(p)
        html = page.get("html", "")
        page["blocks"] = html_to_blocks(html)
        chunks = h2_chunker(page, max_chars=1800)
        out_path = chunks_dir / (p.stem + ".json.gz")
        write_json_gz(out_path, chunks)
        count += 1
    print(f"Transformed {count} pages → {chunks_dir}")

if __name__ == "__main__":
    app()