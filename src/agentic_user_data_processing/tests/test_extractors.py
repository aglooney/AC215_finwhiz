import json
from pathlib import Path

import pytest

from agentic_user_data_processing.services import extraction, extraction_1099, extraction_portfolio


class _DummyLLM:
    def __init__(self, payload: dict):
        self.payload = payload
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.payload)


ROOT_DIR = Path(__file__).resolve().parents[3]


def _assert_llm_called(dummy_llm: _DummyLLM):
    assert dummy_llm.prompts, "LLM was not invoked"


@pytest.mark.asyncio
async def test_extract_w2_fields_with_sample(monkeypatch):
    pdf_path = ROOT_DIR / "src" / "synthetic_data" / "w2" / "outputs" / "w2_000.pdf"
    json_path = pdf_path.with_suffix(".json")
    pdf_bytes = pdf_path.read_bytes()
    source = json.loads(json_path.read_text())

    state_info = source["state_local"][0]
    box12_codes = ";".join(f"{entry['code']}:{entry['amount']}" for entry in source["box12"])
    payload = {
        "employee_name": f"{source['employee']['first_name']} {source['employee']['last_name']}",
        "employee_ssn": source["employee"]["social_security_number"],
        "employer_name": source["employer"]["name_address_block"].splitlines()[0],
        "employer_ein": source["employer"]["ein"],
        "wages_tips_other_comp": str(source["box1_wages"]),
        "federal_income_tax_withheld": str(source["box2_federal_income_tax_withheld"]),
        "social_security_wages": str(source["box3_social_security_wages"]),
        "social_security_tax_withheld": str(source["box4_social_security_tax_withheld"]),
        "medicare_wages": str(source["box5_medicare_wages_tips"]),
        "medicare_tax_withheld": str(source["box6_medicare_tax_withheld"]),
        "box12_codes": box12_codes,
        "state": state_info["state"],
        "state_wages": str(state_info["state_wages"]),
        "state_income_tax": str(state_info["state_income_tax"]),
    }

    dummy = _DummyLLM(payload)
    monkeypatch.setattr(extraction, "_get_llm", lambda: dummy)

    result = await extraction.extract_w2_fields(pdf_bytes)

    for field, value in payload.items():
        assert getattr(result, field) == value
    _assert_llm_called(dummy)


@pytest.mark.asyncio
async def test_extract_1099_fields_with_sample(monkeypatch):
    pdf_path = ROOT_DIR / "src" / "synthetic_data" / "int_1099" / "outputs" / "1099int_001.pdf"
    json_path = pdf_path.with_suffix(".json")
    pdf_bytes = pdf_path.read_bytes()
    source = json.loads(json_path.read_text())

    payload = {
        "box1_interest_income": str(source["box1_interest_income"]),
        "box2_early_withdrawal_penalty": str(source["box2_early_withdrawal_penalty"]),
        "box3_us_savings_bond_interest": str(source["box3_us_savings_bond_interest"]),
        "box4_federal_income_tax_withheld": str(source["box4_federal_income_tax_withheld"]),
        "box5_investment_expenses": str(source["box5_investment_expenses"]),
        "box6_foreign_tax_paid": str(source["box6_foreign_tax_paid"]),
        "box7_foreign_country": source["box7_foreign_country"],
        "box8_tax_exempt_interest": str(source["box8_tax_exempt_interest"]),
        "box9_private_activity_bond_interest": str(source["box9_private_activity_bond_interest"]),
        "box10_market_discount": str(source["box10_market_discount"]),
        "box11_bond_premium": str(source["box11_bond_premium"]),
        "box12_treasury_bond_premium": str(source["box12_treasury_bond_premium"]),
        "box13_tax_exempt_bond_premium": str(source["box13_tax_exempt_bond_premium"]),
        "box14_cusip_number": source["box14_cusip_number"],
        "state": source["state"],
        "state_id": source["state_id"],
        "state_tax_withheld": str(source["state_tax_withheld"]),
    }

    dummy = _DummyLLM(payload)
    monkeypatch.setattr(extraction_1099, "_get_llm", lambda: dummy)

    result = await extraction_1099.extract_1099_fields(pdf_bytes)

    for field, value in payload.items():
        assert getattr(result, field) == value
    _assert_llm_called(dummy)


@pytest.mark.asyncio
async def test_extract_portfolio_fields_with_sample(monkeypatch):
    pdf_path = ROOT_DIR / "src" / "synthetic_data" / "portfolio" / "outputs" / "portfolio_001.pdf"
    json_path = pdf_path.with_suffix(".json")
    pdf_bytes = pdf_path.read_bytes()
    source = json.loads(json_path.read_text())

    holdings_entry = source["holdings"][0]
    payload = {
        "total_portfolio_value": str(source["total_portfolio_value"]),
        "account_name": source["account"]["account_name"],
        "account_number": source["account"]["account_number"],
        "account_type": source["account"]["account_type"],
        "statement_date": source["account"]["statement_date"],
        "account_owner": source["account"]["account_owner"],
        "stocks_percentage": str(source["asset_allocation"]["stocks_percentage"]),
        "bonds_percentage": str(source["asset_allocation"]["bonds_percentage"]),
        "cash_percentage": str(source["asset_allocation"]["cash_percentage"]),
        "other_percentage": str(source["asset_allocation"]["other_percentage"]),
        "holdings": [
            {
                "ticker": holdings_entry["ticker"],
                "name": holdings_entry["name"],
                "shares": str(holdings_entry["shares"]),
                "value": str(holdings_entry["total_value"]),
                "asset_class": holdings_entry["asset_class"],
            }
        ],
        "notes": source["notes"],
    }

    dummy = _DummyLLM(payload)
    monkeypatch.setattr(extraction_portfolio, "_get_llm", lambda: dummy)

    result = await extraction_portfolio.extract_portfolio_fields(pdf_bytes)

    assert result.account_name == payload["account_name"]
    assert result.account_number == payload["account_number"]
    assert result.total_portfolio_value == payload["total_portfolio_value"]
    assert result.stocks_percentage == payload["stocks_percentage"]
    assert result.cash_percentage == payload["cash_percentage"]
    assert result.holdings[0].ticker == payload["holdings"][0]["ticker"]
    assert result.holdings[0].name == payload["holdings"][0]["name"]
    _assert_llm_called(dummy)
