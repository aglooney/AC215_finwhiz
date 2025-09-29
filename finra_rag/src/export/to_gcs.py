from __future__ import annotations
from pathlib import Path
import typer
from google.cloud import storage

app = typer.Typer(add_completion=False)

@app.command()
def main(
    local: str = typer.Option(..., help="Local dir or file to upload"),
    bucket: str = typer.Option(..., help="GCS bucket name (no gs://)"),
    prefix: str = typer.Option("finra/exports/jsonl", help="Prefix in the bucket"),
):
    client = storage.Client()
    b = client.bucket(bucket)

    src = Path(local)
    paths = [p for p in src.rglob("*") if p.is_file()] if src.is_dir() else [src]

    for p in paths:
        rel = p.relative_to(src) if src.is_dir() else Path(p.name)
        dest = f"{prefix}/{rel}".replace("\\", "/")
        blob = b.blob(dest)
        if str(p).endswith(".jsonl.gz"):
            blob.content_type = "application/jsonl+gzip"
            blob.content_encoding = "gzip"
        blob.upload_from_filename(str(p))
        print(f"Uploaded {p} → gs://{bucket}/{dest}")

if __name__ == "__main__":
    app()
