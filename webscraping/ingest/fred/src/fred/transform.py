import json, gzip, argparse
from pathlib import Path

def transform_series(series_file, outdir):
    with open(series_file) as f:
        data = json.load(f)

    # Infer series ID from filename
    series_id = Path(series_file).stem
    observations = data.get("observations", [])

    if not observations:
        print(f"⚠️ No observations found for {series_id}")
        return

    # Latest observation
    last = observations[-1]
    date_str, value = last["date"], last["value"]

    # Create a chunk
    chunk = {
        "id": f"fred-{series_id}-{date_str}",
        "source": f"https://fred.stlouisfed.org/series/{series_id}",
        "title": f"FRED Series {series_id}",
        "content": f"As of {date_str}, {series_id} = {value}."
    }

    # Write as gzipped JSONL
    outfile = Path(outdir) / f"{series_id}.jsonl.gz"
    with gzip.open(outfile, "wt", encoding="utf-8") as f:
        f.write(json.dumps(chunk) + "\n")
    print(f"Transformed {series_id} → {outfile}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="indir", required=True)
    parser.add_argument("--out", dest="outdir", required=True)
    args = parser.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    for file in Path(args.indir).glob("*.json"):
        transform_series(file, args.outdir)

if __name__ == "__main__":
    main()
