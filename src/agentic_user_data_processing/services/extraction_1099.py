"""
Utilities for extracting structured data from uploaded 1099-INT documents.
"""
import asyncio
import json
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_google_vertexai import VertexAI
from google.cloud import aiplatform

from .. import schemas
from . import parser

load_dotenv()

# ---------------------------------------------------------------------
# Gemini prompt (keys match your Form1099Fields schema)
# ---------------------------------------------------------------------

EXTRACTION_PROMPT_1099 = """You are a parsing assistant. Using the supplied 1099-INT text, extract the requested fields.
Return ONLY valid JSON with the exact keys shown. Do not include any explanatory text.

1099-INT text (may be truncated):
{document_text}

Output schema:
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
    """
    Lazy-init a global VertexAI LLM with proper credentials and project.
    """
    global _llm
    if _llm is None:
        creds_path = os.getenv("VERTEXAI_CREDENTIALS")
        if not creds_path:
            raise ValueError("VERTEXAI_CREDENTIALS must be set")

        # Make sure Google client libs see the creds inside the container
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

        # Initialize Vertex AI project/region
        project_id = os.getenv("VERTEXAI_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEXAI_LOCATION", "us-central1")
        if project_id:
            aiplatform.init(project=project_id, location=location)

        _llm = VertexAI(model_name="gemini-2.5-pro")
    return _llm


def _clean_json_text(raw: str) -> str:
    """
    Strip common LLM wrappers (```json ... ```, leading text) and
    return just the content between the first '{' and the last '}'.
    """
    s = str(raw).strip()

    if s.startswith("```"):
        s = s.strip("`").lstrip()
        if s.lower().startswith("json"):
            s = s[4:].lstrip()

    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]

    return s


async def extract_1099_fields(pdf_bytes: bytes) -> schemas.Form1099Fields:
    """
    Parse raw PDF bytes and use Gemini to extract 1099-INT key fields.
    Includes detailed print debugging to trace every stage.
    """
    print("[extract_1099_fields] Starting extraction...")

    # Step 1: Extract text
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

    # Step 2: Build prompt
    prompt = EXTRACTION_PROMPT_1099.format(document_text=document_text[:8000])

    # Step 3: Call Gemini
    try:
        llm = _get_llm()
        print("[extract_1099_fields] Invoking Gemini model...")
        response = await asyncio.to_thread(llm.invoke, prompt)
        print(f"[extract_1099_fields] Raw Gemini response: {response}")

        raw = _clean_json_text(response)
        print(f"[extract_1099_fields] Cleaned JSON text: {raw[:200]}...")

        data = json.loads(raw)
        print(f"[extract_1099_fields] Full parsed JSON: {json.dumps(data, indent=2)}")
        for k, v in data.items():
            print(f"  - {k}: {v!r}")

        return schemas.Form1099Fields(**data)

    except json.JSONDecodeError as e:
        print(f"[extract_1099_fields] JSON decode error: {e}")
        return schemas.Form1099Fields()
    except Exception as e:
        print(f"[extract_1099_fields] General extraction error: {e}")
        return schemas.Form1099Fields()