"""
Robust PDF text extraction test with Ghostscript flattening,
PyPDF + pdfminer fallback, and CID cleanup.

Use this to verify that numeric/text field values in 1099 or W-2 PDFs
are truly visible after flattening.
"""

import subprocess
import io
import re
from pathlib import Path
from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract_text


# === CONFIG ===
INPUT_PDF = Path("src/synthetic_data/int_1099/outputs/1099int_003.pdf")
FLATTENED_PDF = INPUT_PDF.with_name(INPUT_PDF.stem + "_flat.pdf")


# === STEP 1: Flatten PDF with Ghostscript ===
def flatten_pdf(input_path: Path, output_path: Path):
    """Flatten XFA/AcroForm fields into visible text using Ghostscript."""
    print(f"[INFO] Flattening PDF with Ghostscript: {input_path.name}")
    cmd = [
        "gs",
        "-o", str(output_path),
        "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress",
        "-dNOPAUSE",
        "-dBATCH",
        str(input_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[✓] Flattened PDF saved to: {output_path}")
    except FileNotFoundError:
        print("[ERROR] Ghostscript not installed or not found in PATH.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ghostscript flattening failed:\n{e.stderr.decode()}")
        exit(1)


# === STEP 2: Text extraction (PyPDF + pdfminer) ===
def extract_text_from_pdf(path: Path) -> str:
    """Extract text robustly and prefer pdfminer output when richer."""
    # --- PyPDF pass ---
    try:
        buffer = io.BytesIO(path.read_bytes())
        reader = PdfReader(buffer)
        pypdf_text = "\n".join(
            (page.extract_text() or "").strip() for page in reader.pages
        )
        print(f"[INFO] PyPDF text length: {len(pypdf_text)}")
    except Exception as e:
        print(f"[WARN] PyPDF extraction failed: {e}")
        pypdf_text = ""

    # --- Always try pdfminer ---
    try:
        pdfminer_text = pdfminer_extract_text(str(path))
        print(f"[INFO] pdfminer text length: {len(pdfminer_text)}")
    except Exception as e:
        print(f"[ERROR] pdfminer.six extraction failed: {e}")
        pdfminer_text = ""

    # --- Decide which to keep ---
    if len(pdfminer_text.strip()) > len(pypdf_text.strip()) * 1.25:
        print("[INFO] Using pdfminer text (more complete).")
        combined_text = pdfminer_text
    else:
        print("[INFO] Using combined text output (pypdf + pdfminer).")
        combined_text = pypdf_text + "\n\n" + pdfminer_text

    # --- Clean up CID artifacts like (cid:0) ---
    combined_text = re.sub(r"\(cid:\d+\)", "", combined_text)
    return combined_text


# === MAIN TEST ===
if __name__ == "__main__":
    print(f"[INFO] Testing text extraction on: {INPUT_PDF}")

    flatten_pdf(INPUT_PDF, FLATTENED_PDF)

    text = extract_text_from_pdf(FLATTENED_PDF)

    text_clean = " ".join(text.split())
    print(f"[INFO] Raw text length before cleaning: {len(text)}")
    print(f"[SUCCESS] Extracted {len(text_clean)} characters after cleaning.\n")

    print("------ SAMPLE CLEANED TEXT (first 1000 chars) ------")
    print(text_clean[:1000])
    print("---------------------------------------------------")