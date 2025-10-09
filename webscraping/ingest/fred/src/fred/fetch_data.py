import os, requests, json, argparse, yaml
from pathlib import Path
from datetime import date

FRED_API = "https://api.stlouisfed.org/fred"

def fetch_series(series_id, api_key):
    url = f"{FRED_API}/series/observations"
    r = requests.get(url, params={
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json"
    })
    r.raise_for_status()
    return r.json()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    api_key = os.environ["FRED_API_KEY"]
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    with open("config/series.yml") as f:
        series_cfg = yaml.safe_load(f)

    for group, ids in series_cfg.items():
        for sid in ids:
            data = fetch_series(sid, api_key)
            fn = out_path / f"{sid}.json"
            with open(fn, "w") as f:
                json.dump(data, f)
            print(f"Fetched {sid} → {fn}")

if __name__ == "__main__":
    main()