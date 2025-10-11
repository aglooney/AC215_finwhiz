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

EXTRACTION_PROMPT = """You are a parsing assistant. Using the supplied W-2 text, extract the requested fields.
Return ONLY valid JSON with the exact keys shown.

W-2 text (may be truncated):
{document_text}

Output schema:
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

Respond with JSON only.
"""

_llm: Optional[VertexAI] = None


def _get_llm() -> VertexAI:
    global _llm
    if _llm is None:
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS must be set for extraction")
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
        data = json.loads(str(response))
        return schemas.W2Fields(**data)
    except (json.JSONDecodeError, RuntimeError, Exception):
        return schemas.W2Fields()
