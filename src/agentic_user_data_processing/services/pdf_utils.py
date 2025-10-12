"""
PDF utility helpers for preprocessing user uploads.
"""
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def flatten_pdf(data: bytes) -> bytes:
    """
    Attempt to flatten a PDF using pdftk so form fields become static text.
    Returns the original bytes if pdftk is unavailable or the call fails.
    """
    if not data.startswith(b"%PDF"):
        return data

    src_file: Optional[tempfile.NamedTemporaryFile] = None
    dst_file: Optional[tempfile.NamedTemporaryFile] = None

    try:
        src_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        src_file.write(data)
        src_file.flush()
        src_file.close()

        dst_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        dst_file.close()

        subprocess.run(
            ["pdftk", src_file.name, "output", dst_file.name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        flattened = Path(dst_file.name).read_bytes()
        return flattened if flattened else data

    except (FileNotFoundError, subprocess.CalledProcessError):
        return data
    finally:
        if src_file:
            Path(src_file.name).unlink(missing_ok=True)
        if dst_file:
            Path(dst_file.name).unlink(missing_ok=True)
