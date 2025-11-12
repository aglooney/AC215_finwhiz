from pypdf import PdfReader

PDF_PATH = "assets/irs_1099_fillable.pdf"

reader = PdfReader(PDF_PATH)
fields = {}
for page_number, page in enumerate(reader.pages, 1):
    if "/Annots" in page:
        for annot in page["/Annots"]:
            obj = annot.get_object()
            if "/T" in obj:
                fields[obj["/T"]] = page_number

print(f"Found {len(fields)} interactive fields:")
for name, page_number in sorted(fields.items()):
    print(f"Page {page_number}: {name}")
