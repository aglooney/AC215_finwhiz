from __future__ import annotations
from pathlib import Path
import gzip
import typer
import json
from ..common.io_utils import iter_paths, read_json_gz

app = typer.Typer(add_completion=False)

@app.command()
def main(
    _in: str = typer.Option("data/chunks", "--in", help="Dir with per-page chunk json.gz"),
    out: str = typer.Option("data", help="Base data dir"),
    schema: str = typer.Option("config/schema.json"),
):
    out_dir = Path(out) / "exports" / "jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / "finra_chunks.jsonl.gz"

    total = 0
    with gzip.open(fname, "wb") as f:
        for p in iter_paths(_in, ".json.gz"):
            chunks = read_json_gz(p)
            for ch in chunks:
                line = (json.dumps(ch, ensure_ascii=False) + "\n").encode("utf-8")
                f.write(line)
                total += 1
    print(f"Wrote {total} chunks → {fname}")

if __name__ == "__main__":
    app()
