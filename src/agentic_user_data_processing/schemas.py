"""
Pydantic schemas for request/response payloads.
"""
import uuid
from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


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
    box1_interest_income: Optional[Union[float,str]] = None
    box2_early_withdrawal_penalty: Optional[Union[float,str]] = None
    box3_us_savings_bond_interest: Optional[Union[float,str]] = None
    box4_federal_income_tax_withheld: Optional[Union[float,str]] = None
    box5_investment_expenses: Optional[Union[float,str]] = None
    box6_foreign_tax_paid: Optional[Union[float,str]] = None
    box7_foreign_country: Optional[Union[float,str]] = None
    box8_tax_exempt_interest: Optional[Union[float,str]] = None
    box9_private_activity_bond_interest: Optional[Union[float,str]] = None
    box10_market_discount: Optional[Union[float,str]] = None
    box11_bond_premium: Optional[Union[float,str]] = None
    box12_treasury_bond_premium: Optional[Union[float,str]] = None
    box13_tax_exempt_bond_premium: Optional[Union[float,str]] = None
    box14_cusip_number: Optional[Union[float,str]] = None
    state: Optional[Union[float,str]] = None
    state_id: Optional[Union[float,str]] = None
    state_tax_withheld: Optional[Union[float,str]] = None

class SessionContext(BaseModel):
    session_id: str
    user_id: str
    recent_messages: Optional[list[ChatTurn]] = None
    w2_fields: Optional[W2Fields] = None
    form1099_fields: Optional[Form1099Fields] = None
    summary: Optional[str] = None
