from pydantic import BaseModel
from typing import Optional

class Form1099INT(BaseModel):
    payer_name_address: str
    payer_tin: str
    recipient_name_address: str
    recipient_tin: str
    box1_interest_income: float
    box2_early_withdrawal_penalty: Optional[float] = 0.0
    box3_us_savings_bond_interest: Optional[float] = 0.0
    box4_federal_income_tax_withheld: Optional[float] = 0.0
    box5_investment_expenses: Optional[float] = 0.0
    box6_foreign_tax_paid: Optional[float] = 0.0
    box7_foreign_country: Optional[str] = None
    account_number: Optional[str] = None
    state: Optional[str] = None
    state_id: Optional[str] = None
    state_tax_withheld: Optional[float] = 0.0
