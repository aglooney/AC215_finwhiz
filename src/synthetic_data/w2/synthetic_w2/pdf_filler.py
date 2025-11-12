"""PDF form filling helpers for the W-2 template."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError
from pypdf.generic import BooleanObject, NameObject

from .models import W2Record

logger = logging.getLogger(__name__)


@dataclass
class W2PdfFiller:
    """Populate the IRS fillable PDF template using ``W2Record`` data."""

    template_pdf: Path
    field_map: Path
    _cached_map: Dict[str, str] = field(init=False, default_factory=dict)

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    def load_field_map(self) -> Dict[str, str]:
        """Read the logical-to-PDF field mapping from disk (cached)."""

        if not self._cached_map:
            data = yaml.safe_load(self.field_map.read_text())
            if not isinstance(data, dict) or "fields" not in data:
                raise ValueError(
                    f"Field map at {self.field_map} missing 'fields' section"
                )
            fields = data["fields"]
            if not isinstance(fields, dict):
                raise ValueError("'fields' section must be a mapping")
            self._cached_map = {str(k): str(v) for k, v in fields.items()}
        return self._cached_map

    def record_to_fields(self, record: W2Record) -> Dict[str, Any]:
        """Convert a ``W2Record`` into flat field/value pairs for the PDF form."""

        mapping = self.load_field_map()
        values: Dict[str, Any] = {}

        def set_value(logical_key: str, value: Optional[str]) -> None:
            field_name = mapping.get(logical_key)
            if not field_name:
                return
            values[field_name] = value or ""

        def set_amount(logical_key: str, amount: Optional[float]) -> None:
            formatted = f"{amount:.2f}" if amount is not None else ""
            set_value(logical_key, formatted)

        # Employee + Employer identity
        set_value("box_a_employee_ssn", record.employee.social_security_number)
        set_value("box_b_employer_ein", record.employer.ein)
        set_value("box_c_employer_name_address", record.employer.name_address_block)
        set_value("box_d_control_number", record.employer.control_number)
        set_value("employee_first_name", record.employee.first_name)
        set_value("employee_last_name", record.employee.last_name)
        set_value("employee_address_line1", record.employee.address_line1)
        set_value("employee_address_line2", record.employee.address_line2)

        # Core wage boxes
        set_amount("box1_wages_tips_other", record.box1_wages)
        set_amount("box2_federal_income_tax_withheld", record.box2_federal_income_tax_withheld)
        set_amount("box3_social_security_wages", record.box3_social_security_wages)
        set_amount("box4_social_security_tax_withheld", record.box4_social_security_tax_withheld)
        set_amount("box5_medicare_wages_tips", record.box5_medicare_wages_tips)
        set_amount("box6_medicare_tax_withheld", record.box6_medicare_tax_withheld)
        set_amount("box7_social_security_tips", record.box7_social_security_tips)
        set_amount("box8_allocated_tips", record.box8_allocated_tips)
        set_value("box9_verification_code", record.box9_verification_code)
        set_amount("box10_dependent_care_benefits", record.box10_dependent_care_benefits)
        set_amount("box11_nonqualified_plans", record.box11_nonqualified_plans)

        # Box 12 (up to four rows)
        slot_keys = ["a", "b", "c", "d"]
        for idx, slot in enumerate(slot_keys):
            entry = record.box12[idx] if idx < len(record.box12) else None
            set_value(f"box12{slot}_code", entry.code if entry else "")
            set_amount(f"box12{slot}_amount", entry.amount if entry else None)

        # Box 14
        set_value("box14_other", record.box14_other)

        # Checkboxes
        checkbox_mapping = {
            "statutory_employee": "statutory_employee",
            "retirement_plan": "retirement_plan",
            "third_party_sick_pay": "third_party_sick_pay",
        }
        for logical_key, source_key in checkbox_mapping.items():
            field_name = mapping.get(logical_key)
            if not field_name:
                continue
            checked = record.checkboxes.get(source_key, False)
            values[field_name] = "Yes" if checked else "Off"

        # State and local rows (template supports two rows)
        for idx in range(2):
            suffix = idx + 1
            entry = record.state_local[idx] if idx < len(record.state_local) else None
            set_value(f"box15_state_{suffix}", entry.state if entry else "")
            set_value(
                f"box15_state_id_{suffix}",
                entry.state_id if entry else "",
            )
            set_amount(
                f"box16_state_wages_{suffix}",
                entry.state_wages if entry else None,
            )
            set_amount(
                f"box17_state_income_tax_{suffix}",
                entry.state_income_tax if entry else None,
            )
            set_amount(
                f"box18_local_wages_{suffix}",
                entry.local_wages if entry and entry.local_wages is not None else None,
            )
            set_amount(
                f"box19_local_income_tax_{suffix}",
                entry.local_income_tax if entry and entry.local_income_tax is not None else None,
            )
            set_value(
                f"box20_locality_name_{suffix}",
                entry.locality if entry else "",
            )

        return values

    # ------------------------------------------------------------------
    # PDF writing
    # ------------------------------------------------------------------
    def fill_pdf(self, record: W2Record, output_path: Path, flatten: bool = True) -> None:
        """Write a filled PDF to ``output_path`` using the configured template."""

        field_values = self.record_to_fields(record)

        reader = PdfReader(str(self.template_pdf))
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)

        for page in writer.pages:
            try:
                writer.update_page_form_field_values(page, field_values)
            except PyPdfError:
                logger.warning("Skipping form update on page without form fields")

        acro_form = writer._root_object.get("/AcroForm")
        if acro_form is not None:
            acro_form.update({NameObject("/NeedAppearances"): BooleanObject(True)})

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_stream:
            writer.write(output_stream)

        if flatten:
            self._flatten_pdf(output_path)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _flatten_pdf(self, output_path: Path) -> None:
        """Attempt to flatten the PDF using the system pdftk binary if available."""

        pdftk_binary = shutil.which("pdftk")
        if not pdftk_binary:
            logger.warning(
                "pdftk binary not found; generated PDF will remain fillable: %s",
                output_path,
            )
            return

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            subprocess.run(
                [pdftk_binary, str(output_path), "output", str(temp_path), "flatten"],
                check=True,
                capture_output=True,
            )
            shutil.copy2(temp_path, output_path)
        except subprocess.CalledProcessError as exc:
            logger.warning(
                "pdftk flatten failed for %s: %s",
                output_path,
                exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else exc,
            )
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
