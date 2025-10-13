from __future__ import annotations
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

try:
    import orjson
    def dumps(obj: Any) -> bytes:
        return orjson.dumps(obj)
    def loads(b: bytes) -> Any:
        return orjson.loads(b)
except Exception:
    def dumps(obj: Any) -> bytes:
        return json.dumps(obj, ensure_ascii=False).encode("utf-8")
    def loads(b: bytes) -> Any:
        return json.loads(b.decode("utf-8"))

def ensure_dir(p: str | Path) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)

def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_of_text(text: str) -> str:
    return sha256_of_bytes(text.encode("utf-8"))

def write_gzip_bytes(path: str | Path, data: bytes) -> None:
    ensure_dir(Path(path).parent)
    with gzip.open(path, "wb") as f:
        f.write(data)

def read_gzip_bytes(path: str | Path) -> bytes:
    with gzip.open(path, "rb") as f:
        return f.read()

def write_json_gz(path: str | Path, obj: Any) -> None:
    write_gzip_bytes(path, dumps(obj))

def read_json_gz(path: str | Path) -> Any:
    return loads(read_gzip_bytes(path))

def iter_paths(root: str | Path, suffix: str) -> Iterable[Path]:
    base = Path(root)
    yield from base.rglob(f"*{suffix}")