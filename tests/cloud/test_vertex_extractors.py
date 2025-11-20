import os
from pathlib import Path

import pytest

from agentic_user_data_processing.services import extraction, extraction_1099, extraction_portfolio

ROOT_DIR = Path(__file__).resolve().parents[2]
REQUIRES_CREDS = pytest.mark.skipif(
    not os.getenv("VERTEXAI_CREDENTIALS") or not Path(os.getenv("VERTEXAI_CREDENTIALS")).exists(),
    reason="Vertex AI credentials not available",
)


def _load_pdf(path: Path) -> bytes:
    if not path.exists():
        pytest.skip(f"Sample file missing: {path}")
    return path.read_bytes()


@REQUIRES_CREDS
@pytest.mark.asyncio
async def test_w2_extractor_calls_vertex():
    pdf_bytes = _load_pdf(ROOT_DIR / "src" / "synthetic_data" / "w2" / "outputs" / "w2_000.pdf")
    result = await extraction.extract_w2_fields(pdf_bytes)
    assert result.employee_name, "Expected employee name from Vertex extraction"
    assert result.employer_name, "Expected employer name from Vertex extraction"


@REQUIRES_CREDS
@pytest.mark.asyncio
async def test_1099_extractor_calls_vertex():
    pdf_bytes = _load_pdf(ROOT_DIR / "src" / "synthetic_data" / "int_1099" / "outputs" / "1099int_001.pdf")
    result = await extraction_1099.extract_1099_fields(pdf_bytes)
    assert result.box1_interest_income is not None
    assert result.box4_federal_income_tax_withheld is not None


@REQUIRES_CREDS
@pytest.mark.asyncio
async def test_portfolio_extractor_calls_vertex():
    pdf_bytes = _load_pdf(ROOT_DIR / "src" / "synthetic_data" / "portfolio" / "outputs" / "portfolio_001.pdf")
    result = await extraction_portfolio.extract_portfolio_fields(pdf_bytes)
    assert result.total_portfolio_value is not None
    assert result.account_name is not None
