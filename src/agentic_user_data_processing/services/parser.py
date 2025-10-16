"""
PDF parsing helpers.
Now supports flattening with Ghostscript, pdfminer fallback, and CID cleanup.
"""
import io
import re
import subprocess
from pathlib import Path
from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract_text


def extract_text_from_pdf(data: bytes) -> str:
    """
    Fully robust PDF text extraction.

    1. Writes temp file to disk.
    2. Flattens the PDF using Ghostscript (so form values become visible).
    3. Extracts text with both PyPDF and pdfminer.six.
    4. Chooses the richer text source automatically.
    5. Cleans out (cid:xx) artifacts for better LLM parsing.
    """

    # --- Write bytes to temp file ---
    temp_path = Path("/tmp/extract_input.pdf")
    temp_path.write_bytes(data)
    flattened_path = temp_path.with_name("extract_input_flat.pdf")

    # --- Flatten with Ghostscript ---
    print(f"[parser.extract_text_from_pdf] Flattening PDF with Ghostscript...")
    gs_cmd = [
        "gs",
        "-o", str(flattened_path),
        "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress",
        "-dNOPAUSE",
        "-dBATCH",
        str(temp_path),
    ]
    try:
        subprocess.run(gs_cmd, check=True, capture_output=True)
        print(f"[parser.extract_text_from_pdf] Flattened PDF saved to {flattened_path}")
    except FileNotFoundError:
        print("[parser.extract_text_from_pdf][WARN] Ghostscript not found — continuing without flattening.")
        flattened_path = temp_path
    except subprocess.CalledProcessError as e:
        print(f"[parser.extract_text_from_pdf][ERROR] Ghostscript flatten failed: {e}")
        flattened_path = temp_path

    # --- Extract with PyPDF ---
    pypdf_text = ""
    try:
        with open(flattened_path, "rb") as f:
            reader = PdfReader(f)
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
            pypdf_text = "\n".join(pages)
        print(f"[parser.extract_text_from_pdf] PyPDF text length: {len(pypdf_text)}")
    except Exception as e:
        print(f"[parser.extract_text_from_pdf][WARN] PyPDF extraction failed: {e}")

    # --- Extract with pdfminer ---
    pdfminer_text = ""
    try:
        pdfminer_text = pdfminer_extract_text(str(flattened_path))
        print(f"[parser.extract_text_from_pdf] pdfminer text length: {len(pdfminer_text)}")
    except Exception as e:
        print(f"[parser.extract_text_from_pdf][ERROR] pdfminer extraction failed: {e}")

    # --- Choose the better output ---
    if len(pdfminer_text.strip()) > len(pypdf_text.strip()) * 1.25:
        print("[parser.extract_text_from_pdf] Using pdfminer text (more complete).")
        text = pdfminer_text
    else:
        print("[parser.extract_text_from_pdf] Combining PyPDF + pdfminer output.")
        text = pypdf_text + "\n\n" + pdfminer_text

    # --- Cleanup CID noise ---
    text = re.sub(r"\(cid:\d+\)", "", text)
    text = " ".join(text.split())

    print(f"[parser.extract_text_from_pdf] Final cleaned text length: {len(text)}")
    return text