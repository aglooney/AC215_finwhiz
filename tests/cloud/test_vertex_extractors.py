import json
import os
from pathlib import Path

import pytest

from agentic_user_data_processing.services import extraction, extraction_1099, extraction_portfolio

ROOT_DIR = Path(__file__).resolve().parents[2]
REAL_FIXTURE_DIR = Path(os.getenv("REAL_FIXTURE_DIR", ""))
REQUIRES_CREDS = pytest.mark.skipif(
    not os.getenv("VERTEXAI_CREDENTIALS") or not Path(os.getenv("VERTEXAI_CREDENTIALS")).exists(),
    reason="Vertex AI credentials not available",
)


def _load_fixture(fallback_rel: Path, real_name: str) -> tuple[bytes, bool]:
    fallback_path = ROOT_DIR / fallback_rel
    if not fallback_path.exists():
        pytest.skip(f"Fallback fixture missing: {fallback_path}")
    real_path = REAL_FIXTURE_DIR / real_name if REAL_FIXTURE_DIR else None
    if real_path and real_path.exists():
        return real_path.read_bytes(), True
    return fallback_path.read_bytes(), False


@REQUIRES_CREDS
@pytest.mark.asyncio
async def test_w2_extractor_calls_vertex():
    fallback_rel = Path("src") / "synthetic_data" / "w2" / "outputs" / "w2_000.pdf"
    pdf_bytes, is_real = _load_fixture(fallback_rel, "w2_full.pdf")
    source = json.loads((ROOT_DIR / "src" / "synthetic_data" / "w2" / "outputs" / "w2_000.json").read_text())
    result = await extraction.extract_w2_fields(pdf_bytes)
    assert result.employee_name, "Vertex extraction returned empty employee_name"
    assert result.employer_name, "Vertex extraction returned empty employer_name"
    if is_real:
        expected_name = f"{source['employee']['first_name']} {source['employee']['last_name']}"
        assert expected_name in result.employee_name
        employer_prefix = source["employer"]["name_address_block"].splitlines()[0]
        assert employer_prefix in result.employer_name


@REQUIRES_CREDS
@pytest.mark.asyncio
async def test_1099_extractor_calls_vertex():
    fallback_rel = Path("src") / "synthetic_data" / "int_1099" / "outputs" / "1099int_001.pdf"
    pdf_bytes, is_real = _load_fixture(fallback_rel, "1099_full.pdf")
    source = json.loads((ROOT_DIR / "src" / "synthetic_data" / "int_1099" / "outputs" / "1099int_001.json").read_text())
    result = await extraction_1099.extract_1099_fields(pdf_bytes)
    assert result.box1_interest_income, "Vertex extraction returned empty box1_interest_income"
    if is_real:
        assert str(source["box1_interest_income"]).split(".")[0] in str(result.box1_interest_income)
        assert source["recipient_name"].split()[0] in (result.box7_foreign_country or source["box7_foreign_country"])


@REQUIRES_CREDS
@pytest.mark.asyncio
async def test_portfolio_extractor_calls_vertex():
    fallback_rel = Path("src") / "synthetic_data" / "portfolio" / "outputs" / "portfolio_001.pdf"
    pdf_bytes, is_real = _load_fixture(fallback_rel, "portfolio_full.pdf")
    source = json.loads((ROOT_DIR / "src" / "synthetic_data" / "portfolio" / "outputs" / "portfolio_001.json").read_text())
    result = await extraction_portfolio.extract_portfolio_fields(pdf_bytes)
    assert result.total_portfolio_value is not None, "Vertex extraction returned empty total_portfolio_value"
    if is_real:
        assert source["account"]["account_name"] in (result.account_name or "")
        assert source["account"]["account_owner"].split()[0] in (result.account_owner or "")
