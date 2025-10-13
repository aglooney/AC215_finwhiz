from __future__ import annotations
import gzip, json
from pathlib import Path
import argparse

def build_jsonl(in_dir: str, out_dir: str, schema: str):
    in_path = Path(in_dir)
    out_path = Path(out_dir) / "exports/jsonl"
    out_path.mkdir(parents=True, exist_ok=True)
    outfile = out_path / "finra_chunks.jsonl.gz"

    with gzip.open(outfile, "wt", encoding="utf-8") as f:
        for file in in_path.glob("*.json.gz"):
            with gzip.open(file, "rt", encoding="utf-8") as g:
                chunks = json.load(g)
            for ch in chunks:
                f.write(json.dumps(ch) + "\n")

    print(f"Wrote {outfile}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", required=True)
    parser.add_argument("--out", dest="out_dir", required=True)
    parser.add_argument("--schema", required=True)  # not used yet
    args = parser.parse_args()
    build_jsonl(args.in_dir, args.out_dir, args.schema)

if __name__ == "__main__":
    main()