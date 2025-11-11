import yaml
from pypdf import PdfReader

YAML_PATH = "assets/copy_b_field_map.yaml"
PDF_PATH = "assets/irs_1099_fillable.pdf"

def extract_fields(pdf_path):
    reader = PdfReader(pdf_path)
    fields = {}
    for page in reader.pages:
        if "/Annots" in page:
            for annot in page["/Annots"]:
                field = annot.get_object()
                if "/T" in field:
                    fields[field["/T"]] = field
    return fields

def test_all_yaml_fields_exist():
    with open(YAML_PATH, "r") as f:
        mapping = yaml.safe_load(f)["fields"]
    pdf_fields = extract_fields(PDF_PATH)

    missing = [k for k, v in mapping.items() if v not in pdf_fields]
    assert not missing, f"Missing {len(missing)} fields in PDF: {missing}"

if __name__ == "__main__":
    test_all_yaml_fields_exist()
    print("✅ All YAML fields exist in the 1099 PDF.")
