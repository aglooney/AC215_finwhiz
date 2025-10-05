"""Data models for synthetic W-2 records."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmployeeInfo(BaseModel):
    """Simple container for employee-facing fields on the W-2."""

    first_name: str
    last_name: str
    address_line1: str
    address_line2: str
    social_security_number: str


class EmployerInfo(BaseModel):
    """Employer identification details printed on the W-2."""

    name_address_block: str
    ein: str
    control_number: Optional[str] = None


class Box12Entry(BaseModel):
    """Represents one code/amount pair in box 12."""

    code: str = Field(max_length=2)
    amount: float


class StateLocalEntry(BaseModel):
    """Captures state and local tax information for one row of boxes 15–20."""

    state: str
    state_id: str
    state_wages: float
    state_income_tax: float
    local_wages: Optional[float] = None
    local_income_tax: Optional[float] = None
    locality: Optional[str] = None


class W2Record(BaseModel):
    """Pydantic model describing the full W-2 document payload."""

    tax_year: int
    employee: EmployeeInfo
    employer: EmployerInfo
    box1_wages: float
    box2_federal_income_tax_withheld: float
    box3_social_security_wages: float
    box4_social_security_tax_withheld: float
    box5_medicare_wages_tips: float
    box6_medicare_tax_withheld: float
    box7_social_security_tips: Optional[float] = None
    box8_allocated_tips: Optional[float] = None
    box9_verification_code: Optional[str] = None
    box10_dependent_care_benefits: Optional[float] = None
    box11_nonqualified_plans: Optional[float] = None
    box12: List[Box12Entry] = Field(default_factory=list)
    box14_other: Optional[str] = None
    checkboxes: Dict[str, bool] = Field(default_factory=dict)
    state_local: List[StateLocalEntry] = Field(default_factory=list)
    additional_fields: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation for downstream storage."""

        return self.model_dump()
