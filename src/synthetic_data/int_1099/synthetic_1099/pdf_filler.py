# synthetic_1099/pdf_filler.py
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
import yaml
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# ---------- Path Constants ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_TEMPLATE_PDF = PROJECT_ROOT / "assets" / "irs_1099_fillable.pdf"
DEFAULT_FIELD_MAP = PROJECT_ROOT / "assets" / "copy_b_field_map.yaml"

# ---------- Core PDF Filling ----------
def fill_pdf(data: dict, output_path: Path = None):
    """Fill the IRS 1099-INT Copy B PDF using the YAML field map."""
    pdf_template = DEFAULT_TEMPLATE_PDF
    field_map_path = DEFAULT_FIELD_MAP

    # Ensure output directory exists
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "filled_1099int.pdf"

    # Load mapping and template
    with open(field_map_path, "r") as f:
        mapping = yaml.safe_load(f)["fields"]

    reader = PdfReader(str(pdf_template))
    writer = PdfWriter()

    # Copy pages
    for page in reader.pages:
        writer.add_page(page)

    # Preserve AcroForm
    if reader.trailer.get("/Root").get("/AcroForm"):
        writer._root_object.update({
            NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
        })

    # Fill form fields
    writer.update_page_form_field_values(
        writer.pages[0],
        {field_path: str(data[key]) for key, field_path in mapping.items() if key in data}
    )

    # Write the new PDF
    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    return output_path


# ---------- Optional Convenience Wrappers ----------
def load_yaml(path: Path) -> dict:
    """Utility to load YAML files safely."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def fill_1099int(output_path: Path, form_data: dict):
    """
    Wrapper to fill a 1099-INT Copy B using the default template and field map.
    form_data: a dictionary or Pydantic model dict() containing all required fields.
    """
    field_map = load_yaml(DEFAULT_FIELD_MAP)["fields"]
    reader = PdfReader(str(DEFAULT_TEMPLATE_PDF))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])

    for key, field_path in field_map.items():
        if key in form_data:
            try:
                writer.update_page_form_field_values(
                    writer.pages[0], {field_path: str(form_data[key])}
                )
            except Exception as e:
                print(f"[!] Could not fill field '{key}' ({field_path}): {e}")

    with open(output_path, "wb") as f_out:
        writer.write(f_out)
    return output_path