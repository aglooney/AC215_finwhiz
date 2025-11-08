"""
Utilities for extracting structured data from uploaded Fidelity portfolio summaries.
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

EXTRACTION_PROMPT_PORTFOLIO = """You are a parsing assistant. Using the supplied Fidelity portfolio summary text, extract the requested fields.
Return ONLY valid JSON with the exact keys shown. If a field is not found, use null or an empty array for holdings.

Portfolio summary text (may be truncated):
{document_text}

Output schema:
{{
  "total_portfolio_value": "",
  "account_name": "",
  "account_number": "",
  "account_type": "",
  "statement_date": "",
  "account_owner": "",
  "stocks_percentage": "",
  "bonds_percentage": "",
  "cash_percentage": "",
  "other_percentage": "",
  "holdings": [
    {{
      "ticker": "",
      "name": "",
      "shares": "",
      "value": "",
      "asset_class": ""
    }}
  ],
  "notes": ""
}}

IMPORTANT INSTRUCTIONS:
- Extract total portfolio value, account information, and statement date with high priority
- For asset allocation percentages, extract if clearly stated (e.g., "60% stocks, 30% bonds, 10% cash")
- For holdings array: only include if individual positions are clearly listed with ticker symbols
- If holdings are unclear or ambiguous, return an empty array [] rather than guessing
- Use the "notes" field for any additional context that might be useful for financial education
- For numeric fields, you can use either numbers or strings (e.g., "10000.50" or 10000.50)
- Be conservative: prefer accuracy over completeness

Respond with JSON only.
"""

_llm: Optional[VertexAI] = None


def _get_llm() -> VertexAI:
    """
    Lazy-init a global VertexAI LLM with proper credentials and project.
    Matches W-2 and 1099 extractor structure exactly.
    """
    global _llm
    if _llm is None:
        VERTEXAI_CREDENTIALS = os.getenv("VERTEXAI_CREDENTIALS")
        if not VERTEXAI_CREDENTIALS:
            raise ValueError("VERTEXAI_CREDENTIALS must be set")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS
        _llm = VertexAI(model_name="gemini-2.5-pro")
        print("[_get_llm] Initialized VertexAI model (gemini-2.5-pro) for portfolio extraction")
    return _llm


async def extract_portfolio_fields(pdf_bytes: bytes) -> schemas.PortfolioFields:
    """
    Parse raw PDF bytes and use Gemini to extract Fidelity portfolio summary key fields.
    
    This function prioritizes high-level metrics (total value, account info, asset allocation)
    and only extracts holdings when they are clearly structured in the document.
    
    If credentials are missing or parsing fails, return an empty schema
    so the application can continue operating.
    """
    print("[extract_portfolio_fields] Starting portfolio extraction...")

    # Step 1: Extract text from PDF
    try:
        document_text = parser.extract_text_from_pdf(pdf_bytes)
        print(f"[extract_portfolio_fields] Extracted {len(document_text)} characters of text")
    except Exception as e:
        print(f"[extract_portfolio_fields] Failed to extract text: {e}")
        document_text = ""

    if not document_text:
        print("[extract_portfolio_fields] No text found, returning empty schema")
        return schemas.PortfolioFields()

    print(f"[extract_portfolio_fields] Sample extracted text (first 600 chars):\n{document_text[:600]}")

    # Step 2: Build prompt (truncate for safety, but allow more text for portfolios)
    prompt = EXTRACTION_PROMPT_PORTFOLIO.format(document_text=document_text[:8000])
    print(f"[extract_portfolio_fields] Built prompt of length {len(prompt)} characters")

    # Step 3: Call Gemini
    try:
        llm = _get_llm()
        print("[extract_portfolio_fields] Invoking Gemini model...")
        response = await asyncio.to_thread(llm.invoke, prompt)
        print(f"[extract_portfolio_fields] Raw Gemini response: {response}")

        raw = str(response).strip()
        
        # Clean markdown code fences if present
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()

        print(f"[extract_portfolio_fields] Cleaned response (first 300 chars): {raw[:300]}")

        data = json.loads(raw)
        print(f"[extract_portfolio_fields] Parsed JSON keys: {list(data.keys())}")

        # Log extracted values for debugging
        for k, v in data.items():
            if k != "holdings":  # Don't spam with holdings details
                print(f"  - {k}: {v!r}")
            else:
                holdings_count = len(v) if v else 0
                print(f"  - holdings: [{holdings_count} positions]")

        print("[extract_portfolio_fields] Returning populated PortfolioFields object")
        return schemas.PortfolioFields(**data)

    except (json.JSONDecodeError, RuntimeError, Exception) as e:
        print(f"[extract_portfolio_fields] Extraction failed with error: {e}")
        return schemas.PortfolioFields()

