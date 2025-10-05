"""Command-line interface for the synthetic W-2 generator."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import typer

from .generator import W2RecordGenerator
from .pdf_filler import W2PdfFiller


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_TEMPLATE_PDF = PROJECT_ROOT / "assets" / "irs_w-2_fillable.pdf"
DEFAULT_FIELD_MAP = PROJECT_ROOT / "assets" / "copy_b_field_map.yaml"


def generate(
    output_dir: Path = typer.Option(
        DEFAULT_OUTPUT_DIR,
        help="Directory where generated artifacts should be written.",
    ),
    count: int = typer.Option(1, min=1, help="Number of synthetic W-2 records to create."),
    seed: Optional[int] = typer.Option(None, help="Deterministic seed for reproducibility."),
    template_pdf: Path = typer.Option(
        DEFAULT_TEMPLATE_PDF,
        help="Path to the fillable W-2 PDF template.",
    ),
    field_map: Path = typer.Option(
        DEFAULT_FIELD_MAP,
        help="YAML mapping of logical fields to PDF form names.",
    ),
    flatten: bool = typer.Option(
        True,
        help="Flatten the resulting PDF so form fields become static text.",
    ),
) -> None:
    """Generate W-2 PDFs and JSON artifacts using the configured pipeline."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    output_dir = output_dir.expanduser().resolve()
    template_pdf = template_pdf.expanduser().resolve()
    field_map = field_map.expanduser().resolve()

    if not template_pdf.exists():
        raise typer.BadParameter(
            f"Template PDF not found: {template_pdf}",
            param_hint="template-pdf",
        )
    if not field_map.exists():
        raise typer.BadParameter(
            f"Field map not found: {field_map}",
            param_hint="field-map",
        )

    generator = W2RecordGenerator(seed=seed)
    filler = W2PdfFiller(template_pdf=template_pdf, field_map=field_map)

    output_dir.mkdir(parents=True, exist_ok=True)

    for index in range(count):
        record = generator.build_record()
        record_path = output_dir / f"w2_{index:03d}.json"
        record_path.write_text(json.dumps(record.to_dict(), indent=2))
        pdf_path = output_dir / f"w2_{index:03d}.pdf"
        filler.fill_pdf(
            record=record,
            output_path=pdf_path,
            flatten=flatten,
        )
        typer.echo(
            f"Generated {record_path.name} and {pdf_path.name} | wages: ${record.box1_wages:,.2f}"
        )


def main() -> None:
    """Entry-point for ``python -m synthetic_w2``."""

    typer.run(generate)


if __name__ == "__main__":  # pragma: no cover - module execution guard
    main()
