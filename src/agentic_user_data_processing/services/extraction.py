"""
Utilities for extracting structured data from uploaded documents.
"""
import asyncio
import json
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_google_vertexai import VertexAI

from .. import schemas
from . import parser

load_dotenv()

# ---------------------------------------------------------------------
# GEMINI prompt
# ---------------------------------------------------------------------
EEXTRACTION_PROMPT = """You are a parsing assistant. Using the supplied text, extract the requested fields. First identify whether the document is a 1099-INT or a W2.
Second, return ONLY valid JSON with the exact keys shown corresponding to the document tyupe.

Omit any fields you cannot find.

{document_text}

IF W-2, make this output schema:
{{
  "employee_name": "",
  "employee_ssn": "",
  "employer_name": "",
  "employer_ein": "",
  "wages_tips_other_comp": "",
  "federal_income_tax_withheld": "",
  "social_security_wages": "",
  "social_security_tax_withheld": "",
  "medicare_wages": "",
  "medicare_tax_withheld": "",
  "box12_codes": "",
  "state": "",
  "state_wages": "",
  "state_income_tax": ""
}}

IF 1099-INT, make this output schema:
{{
  "payer_name": "",
  "payer_address": "",
  "payer_tin": "",
  "recipient_name": "",
  "recipient_address": "",
  "recipient_tin": "",
  "interest_income": "",
  "nonemployee_comp": "",
  "fed_tax_withheld": "",
  "state_tax_withheld": "",
  "state_number": "",
  "state_income": "",
  "rents": "",
  "royalties": "",
  "other_income": "",
  "medical_healthcare_payments": "",
  "substitute_payments": "",
  "crop_insurance_proceeds": "",
  "gross_proceeds_paid": ""
}}

Respond with JSON only.
"""

_llm: Optional[VertexAI] = None


def _get_llm() -> VertexAI:
    global _llm
    if _llm is None:
        VERTEXAI_CREDENTIALS = os.getenv("VERTEXAI_CREDENTIALS")
        if not VERTEXAI_CREDENTIALS:
            raise ValueError("VERTEXAI_CREDENTIALS must be set")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS
        _llm = VertexAI(model_name="gemini-2.5-pro")
    return _llm


async def extract_w2_fields(pdf_bytes: bytes) -> schemas.W2Fields:
    """
    Parse raw PDF bytes and use Gemini to extract key fields.

    If credentials are missing or parsing fails, return an empty schema
    so the application can continue operating.
    """
    try:
        document_text = parser.extract_text_from_pdf(pdf_bytes)
    except Exception:
        document_text = ""

    if not document_text:
        return schemas.W2Fields()

    prompt = EXTRACTION_PROMPT.format(document_text=document_text[:4000])

    try:
        llm = _get_llm()
        response = await asyncio.to_thread(llm.invoke, prompt)
        raw = str(response).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()
        data = json.loads(raw)
        return schemas.W2Fields(**data)
    except (json.JSONDecodeError, RuntimeError, Exception):
        return schemas.W2Fields()
    