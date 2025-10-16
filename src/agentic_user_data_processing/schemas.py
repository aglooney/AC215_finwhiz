"""
Pydantic schemas for request/response payloads.
"""
import uuid
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_id: uuid.UUID


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    document_type: str
    gcs_uri: str
    raw_metadata: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class W2Fields(BaseModel):
    employee_name: Optional[str] = None
    employee_ssn: Optional[str] = None
    employer_name: Optional[str] = None
    employer_ein: Optional[str] = None
    wages_tips_other_comp: Optional[str] = None
    federal_income_tax_withheld: Optional[str] = None
    social_security_wages: Optional[str] = None
    social_security_tax_withheld: Optional[str] = None
    medicare_wages: Optional[str] = None
    medicare_tax_withheld: Optional[str] = None
    box12_codes: Optional[str] = None
    state: Optional[str] = None
    state_wages: Optional[str] = None
    state_income_tax: Optional[str] = None

class Form1099Fields(BaseModel):
    payer_name_address: Optional[str] = None
    payer_tin: Optional[str] = None
    recipient_name_address: Optional[str] = None
    recipient_tin: Optional[str] = None
    interest_income: Optional[str] = None
    federal_income_tax_withheld: Optional[str] = None
    state_tax_withheld: Optional[str] = None
    state: Optional[str] = None
    state_id_number: Optional[str] = None

class SessionContext(BaseModel):
    session_id: uuid.UUID
    user_id: uuid.UUID
    recent_messages: List[ChatTurn]
    w2_fields: Optional[W2Fields] = None
    summary: Optional[str] = None
