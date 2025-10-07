"""Synthetic data generation logic for W-2 documents."""

from __future__ import annotations

from dataclasses import dataclass, field
import string
from typing import List, Optional

import numpy as np
from faker import Faker

from .models import (
    Box12Entry,
    EmployeeInfo,
    EmployerInfo,
    StateLocalEntry,
    W2Record,
)

SOCIAL_SECURITY_WAGE_BASE = 168_600.0
_401K_CONTRIBUTION_LIMIT = 23_000.0
_DEFAULT_TAX_YEAR = 2025


@dataclass
class W2RecordGenerator:
    """Emit deterministic-yet-realistic synthetic ``W2Record`` instances."""

    seed: Optional[int] = None
    locale: str = "en_US"
    _faker: Faker = field(init=False)
    _rng: np.random.Generator = field(init=False)

    def __post_init__(self) -> None:
        self._faker = Faker(self.locale)
        if self.seed is not None:
            # Seed both Faker and the numpy RNG for reproducibility.
            self._faker.seed_instance(self.seed)
            self._rng = np.random.default_rng(self.seed)
        else:
            self._rng = np.random.default_rng()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_record(self) -> W2Record:
        """Create a single synthetic ``W2Record`` instance."""

        tax_year = _DEFAULT_TAX_YEAR
        employer = self._build_employer()
        employee, employee_state = self._build_employee()

        wages = float(self._rng.uniform(45_000, 195_000))
        wages = round(wages, 2)
        federal_withholding = round(wages * self._rng.uniform(0.12, 0.32), 2)

        social_security_wages = round(min(wages, SOCIAL_SECURITY_WAGE_BASE), 2)
        social_security_tax = round(social_security_wages * 0.062, 2)

        medicare_wages = wages
        medicare_tax_rate = 0.0145 + (0.009 if wages > 200_000 else 0)
        medicare_tax = round(medicare_wages * medicare_tax_rate, 2)

        # Optional income categories.
        social_security_tips = self._maybe_amount(0, 8_000)
        allocated_tips = self._maybe_amount(0, 2_500)
        dependent_care = self._maybe_amount(0, 5_000)
        nonqualified_plans = self._maybe_amount(0, 7_500)

        # Box 12 entries (up to 4 rows on the template).
        box12_entries = self._build_box12_entries(wages)
        retirement_plan_flag = any(entry.code == "D" for entry in box12_entries)

        checkbox_flags = {
            "statutory_employee": bool(self._rng.binomial(1, 0.05)),
            "retirement_plan": retirement_plan_flag,
            "third_party_sick_pay": bool(self._rng.binomial(1, 0.08)),
        }

        state_rows = self._build_state_rows(wages, employee_state)

        additional_fields = {
            "medicare_tax_rate": medicare_tax_rate,
            "federal_withholding_rate": federal_withholding / wages if wages else 0,
        }

        return W2Record(
            tax_year=tax_year,
            employee=employee,
            employer=employer,
            box1_wages=wages,
            box2_federal_income_tax_withheld=federal_withholding,
            box3_social_security_wages=social_security_wages,
            box4_social_security_tax_withheld=social_security_tax,
            box5_medicare_wages_tips=medicare_wages,
            box6_medicare_tax_withheld=medicare_tax,
            box7_social_security_tips=social_security_tips,
            box8_allocated_tips=allocated_tips,
            box9_verification_code=self._build_verification_code(),
            box10_dependent_care_benefits=dependent_care,
            box11_nonqualified_plans=nonqualified_plans,
            box12=box12_entries,
            box14_other=self._build_box14_note(),
            checkboxes=checkbox_flags,
            state_local=state_rows,
            additional_fields=additional_fields,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_employer(self) -> EmployerInfo:
        company_name = self._faker.company()
        street = self._faker.street_address()
        city = self._faker.city()
        state = self._faker.state_abbr()
        zipcode = self._faker.zipcode()
        name_address = f"{company_name}\n{street}\n{city}, {state} {zipcode}"
        ein = self._faker.ein()
        control_number = (
            f"{self._rng.integers(100000, 999999)}"
            if self._rng.binomial(1, 0.4)
            else None
        )
        return EmployerInfo(
            name_address_block=name_address,
            ein=ein,
            control_number=control_number,
        )

    def _build_employee(self) -> tuple[EmployeeInfo, str]:
        first = self._faker.first_name()
        last = self._faker.last_name()
        street = self._faker.street_address()
        city = self._faker.city()
        state = self._faker.state_abbr()
        zipcode = self._faker.postcode()
        ssn = self._faker.ssn()
        address_line1 = street
        address_line2 = f"{city}, {state} {zipcode}"
        employee = EmployeeInfo(
            first_name=first,
            last_name=last,
            address_line1=address_line1,
            address_line2=address_line2,
            social_security_number=ssn,
        )
        return employee, state

    def _maybe_amount(self, low: float, high: float) -> Optional[float]:
        if self._rng.binomial(1, 0.3) == 0:
            return None
        return round(float(self._rng.uniform(low, high)), 2)

    def _build_box12_entries(self, wages: float) -> List[Box12Entry]:
        entries: List[Box12Entry] = []

        # Box 12 code D: Elective deferrals to 401(k).
        contribution = wages * self._rng.uniform(0.03, 0.08)
        contribution = min(contribution, _401K_CONTRIBUTION_LIMIT)
        contribution = round(contribution, 2)
        if contribution >= 200.0:  # Skip negligible amounts.
            entries.append(Box12Entry(code="D", amount=contribution))

        # Optional employer-sponsored health coverage (code DD).
        if self._rng.binomial(1, 0.7):
            coverage = round(float(self._rng.uniform(3_000, 12_000)), 2)
            entries.append(Box12Entry(code="DD", amount=coverage))

        # Optional HSA contributions (code W).
        if self._rng.binomial(1, 0.25):
            hsa = round(float(self._rng.uniform(500, 3_850)), 2)
            entries.append(Box12Entry(code="W", amount=hsa))

        # Limit to four entries to match fields available on the template.
        return entries[:4]

    def _build_state_rows(self, wages: float, primary_state: str) -> List[StateLocalEntry]:
        rows: List[StateLocalEntry] = []
        tax_rate = self._rng.uniform(0.03, 0.065)
        state_id_number = ''.join(str(self._rng.integers(0, 9)) for _ in range(9))
        state_income_tax = round(wages * tax_rate, 2)

        local_wages: Optional[float] = None
        local_tax: Optional[float] = None
        locality: Optional[str] = None
        if self._rng.binomial(1, 0.2):
            locality = self._faker.city()
            local_wages = round(wages * self._rng.uniform(0.4, 1.0), 2)
            local_tax = round(local_wages * self._rng.uniform(0.01, 0.025), 2)

        rows.append(
            StateLocalEntry(
                state=primary_state,
                state_id=state_id_number,
                state_wages=round(wages, 2),
                state_income_tax=state_income_tax,
                local_wages=local_wages,
                local_income_tax=local_tax,
                locality=locality,
            )
        )

        # Optional second state (e.g., mid-year relocation).
        if self._rng.binomial(1, 0.15):
            secondary_state = self._faker.state_abbr()
            ratio = self._rng.uniform(0.2, 0.6)
            wages_secondary = round(wages * ratio, 2)
            tax_rate_secondary = self._rng.uniform(0.025, 0.07)
            state_income_tax_secondary = round(
                wages_secondary * tax_rate_secondary,
                2,
            )
            state_id_secondary = ''.join(
                str(self._rng.integers(0, 9)) for _ in range(9)
            )
            rows.append(
                StateLocalEntry(
                    state=secondary_state,
                    state_id=state_id_secondary,
                    state_wages=wages_secondary,
                    state_income_tax=state_income_tax_secondary,
                    local_wages=None,
                    local_income_tax=None,
                    locality=None,
                )
            )

        return rows[:2]

    def _build_verification_code(self) -> str:
        letters = ''.join(self._rng.choice(list(string.ascii_uppercase), size=4).tolist())
        digits = ''.join(str(self._rng.integers(0, 9)) for _ in range(4))
        return f"{letters}{digits}"

    def _build_box14_note(self) -> Optional[str]:
        if self._rng.binomial(1, 0.4) == 0:
            return None
        descriptors = [
            "Union dues",
            "Charity",
            "Parking",
            "Tuition",
            "ESP Stock",
        ]
        label = self._rng.choice(descriptors)
        amount = round(float(self._rng.uniform(150, 2_500)), 2)
        return f"{label}: ${amount:,.2f}"
