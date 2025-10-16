"""
Utilities for extracting structured data from uploaded 1099-INT documents.
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

EXTRACTION_PROMPT_1099 = """You are a parsing assistant. Using the supplied 1099-INT text, extract only the fields defined below.
Return ONLY valid JSON with the exact keys shown — no explanations or text outside the JSON.

1099-INT text (may be truncated):
{document_text}

Output schema:
{{
  "box1_interest_income": "",
  "box2_early_withdrawal_penalty": "",
  "box3_us_savings_bond_interest": "",
  "box4_federal_income_tax_withheld": "",
  "box5_investment_expenses": "",
  "box6_foreign_tax_paid": "",
  "box7_foreign_country": "",
  "box8_tax_exempt_interest": "",
  "box9_private_activity_bond_interest": "",
  "box10_market_discount": "",
  "box11_bond_premium": "",
  "box12_treasury_bond_premium": "",
  "box13_tax_exempt_bond_premium": "",
  "box14_cusip_number": "",
  "state": "",
  "state_id": "",
  "state_tax_withheld": ""
}}

Respond with JSON only.
"""

_llm: Optional[VertexAI] = None


def _get_llm() -> VertexAI:
    """
    Lazy-init a global VertexAI LLM with proper credentials and project.
    Matches W-2 extractor structure exactly.
    """
    global _llm
    if _llm is None:
        VERTEXAI_CREDENTIALS = os.getenv("VERTEXAI_CREDENTIALS")
        if not VERTEXAI_CREDENTIALS:
            raise ValueError("VERTEXAI_CREDENTIALS must be set")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS
        _llm = VertexAI(model_name="gemini-2.5-pro")
        print("[_get_llm] Initialized VertexAI model (gemini-2.5-pro)")
    return _llm

async def extract_1099_fields(pdf_bytes: bytes) -> schemas.Form1099Fields:
    """
    Parse raw PDF bytes and use Gemini to extract 1099-INT key fields.
    Mirrors W-2 logic but with detailed print debugging.
    """
    print("[extract_1099_fields] Starting extraction...")

    # Step 1: Extract text from PDF
    try:
        document_text = parser.extract_text_from_pdf(pdf_bytes)
        print(f"[extract_1099_fields] Extracted {len(document_text)} characters of text")
    except Exception as e:
        print(f"[extract_1099_fields] Failed to extract text: {e}")
        document_text = ""

    if not document_text:
        print("[extract_1099_fields] No text found, returning empty schema")
        return schemas.Form1099Fields()

    print(f"[extract_1099_fields] Sample extracted text (first 600 chars):\n{document_text[:600]}")

    # Step 2: Build prompt (truncate for safety)
    prompt = EXTRACTION_PROMPT_1099.format(document_text=document_text[:4000])
    print(f"[extract_1099_fields] Built prompt of length {len(prompt)} characters")

    # Step 3: Call Gemini
    try:
        llm = _get_llm()
        print("[extract_1099_fields] Invoking Gemini model...")
        response = await asyncio.to_thread(llm.invoke, prompt)
        print(f"[extract_1099_fields] Raw Gemini response: {response}")

        raw = str(response).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()

        print(f"[extract_1099_fields] Cleaned response (first 200 chars): {raw[:200]}")

        data = json.loads(raw)
        print(f"[extract_1099_fields] Parsed JSON keys: {list(data.keys())}")

        for k, v in data.items():
            print(f"  - {k}: {v!r}")

        print("[extract_1099_fields] Returning populated Form1099Fields object")
        return schemas.Form1099Fields(**data)

    except (json.JSONDecodeError, RuntimeError, Exception) as e:
        print(f"[extract_1099_fields] Extraction failed with error: {e}")
        return schemas.Form1099Fields()