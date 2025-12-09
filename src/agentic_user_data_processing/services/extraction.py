"""
Utilities for extracting structured data from uploaded documents.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_google_vertexai import VertexAI

from .. import schemas
from . import parser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def _extract_json_from_response(raw: str) -> dict:
    """Extract JSON from model response, handling various formats."""
    text = raw.strip()

    # Remove markdown code blocks like ```json ... ```
    if "```" in text:
        # Find content between code fences
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in response using greedy match
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("Could not extract JSON from response", text, 0)


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
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        document_text = ""

    if not document_text:
        logger.warning("No text extracted from PDF")
        return schemas.W2Fields()

    prompt = EXTRACTION_PROMPT.format(document_text=document_text[:4000])
    raw = None

    try:
        llm = _get_llm()
        response = await asyncio.to_thread(llm.invoke, prompt)
        raw = str(response).strip()

        # Save raw response for CI debugging
        try:
            Path("/tmp/vertex_w2_response.json").write_text(raw)
        except Exception:
            pass

        logger.info(f"Vertex raw response (first 500 chars): {raw[:500]}")

        data = _extract_json_from_response(raw)
        result = schemas.W2Fields(**data)

        # Log if critical fields are empty
        if not result.employee_name:
            logger.warning(f"employee_name is empty after parsing. Raw: {raw[:1000]}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}. Raw response: {raw[:1000] if raw else 'N/A'}")
        return schemas.W2Fields()
    except Exception as e:
        logger.error(f"W2 extraction failed: {e}. Raw response: {raw[:500] if raw else 'N/A'}")
        return schemas.W2Fields()
