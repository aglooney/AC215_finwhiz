# synthetic_1099/generator.py
from pathlib import Path
import json
import random
from faker import Faker
from .pdf_filler import fill_pdf, DEFAULT_OUTPUT_DIR

# ---------- Path Constants ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"

faker = Faker("en_US")

# ---------- Core Generator ----------
def generate_1099_records(n: int = 1, seed: int = 42, output_dir: Path = DEFAULT_OUTPUT_DIR):
    """
    Generate synthetic IRS 1099-INT forms and matching JSON metadata.
    :param n: number of records to generate
    :param seed: random seed for reproducibility
    :param output_dir: output directory path
    """
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, n + 1):
        # --- Synthetic but realistic data ---
        payer_name = faker.company()
        payer_address = faker.street_address()
        payer_city = faker.city()
        payer_state = faker.state_abbr()
        payer_zip = faker.zipcode()

        recipient_name = faker.name()
        recipient_address = faker.street_address()
        recipient_city = faker.city()
        recipient_state = faker.state_abbr()
        recipient_zip = faker.zipcode()

        # --- Boxes 1–14 (realistic financial values) ---
        # Box 1 is total interest income (the anchor value for the rest)
        box1 = round(random.uniform(100.0, 5000.0), 2)
        # Penalty for early withdrawal: usually ≤ 10 % of total interest
        box2 = round(box1 * random.uniform(0.0, 0.10), 2)
        # U.S. savings bond interest: typically 0–30 % of total
        box3 = round(box1 * random.uniform(0.0, 0.30), 2)
        # Federal income tax withheld: generally 5–25 % of total interest
        box4 = round(box1 * random.uniform(0.05, 0.25), 2)
        # Investment expenses: typically small relative to earnings
        box5 = round(box1 * random.uniform(0.00, 0.05), 2)
        # Foreign tax paid: 0–10 % depending on residency
        box6 = round(box1 * random.uniform(0.00, 0.10), 2)
        # Country where foreign tax was paid (almost always USA here)
        box7 = "USA"
        # Tax-exempt interest: often 0–40 % of total, depends on bond type
        box8 = round(box1 * random.uniform(0.00, 0.40), 2)
        # Private activity bond interest: subset of tax-exempt interest
        box9 = round(box8 * random.uniform(0.00, 0.20), 2)
        # Market discount: small portion of total income
        box10 = round(box1 * random.uniform(0.00, 0.05), 2)
        # Bond premium: generally reduces taxable interest (negative offset)
        box11 = round(box1 * random.uniform(0.00, 0.15), 2)
        # Treasury bond premium: subset of bond premium
        box12 = round(box11 * random.uniform(0.00, 0.60), 2)
        # Tax-exempt bond premium: subset of bond premium too
        box13 = round(box11 * random.uniform(0.00, 0.40), 2)
        # CUSIP number: 9-character security identifier
        box14 = faker.swift8()

        record = {
            # Payer / Recipient data
            "payer_name_address": f"{payer_name}, {payer_address}, {payer_city}, {payer_state} {payer_zip}, USA",
            "payer_tin": faker.ssn(),
            "recipient_name": recipient_name,
            "recipient_tin": faker.ssn(),
            "recipient_address": recipient_address,
            "recipient_city": recipient_city,
            "recipient_state": recipient_state,
            "recipient_zip": recipient_zip,
            "recipient_city_state_zip": f"{recipient_city}, {recipient_state} {recipient_zip}",
            "recipient_name_address": f"{recipient_address}, {recipient_city}, {recipient_state} {recipient_zip}, USA",
            "account_number": str(random.randint(10000000, 99999999)),
            "foreign_country": "USA",
            
            # Financial boxes 1–14
            "box1_interest_income": box1,
            "box2_early_withdrawal_penalty": box2,
            "box3_us_savings_bond_interest": box3,
            "box4_federal_income_tax_withheld": box4,
            "box5_investment_expenses": box5,
            "box6_foreign_tax_paid": box6,
            "box7_foreign_country": box7,
            "box8_tax_exempt_interest": box8,
            "box9_private_activity_bond_interest": box9,
            "box10_market_discount": box10,
            "box11_bond_premium": box11,
            "box12_treasury_bond_premium": box12,
            "box13_tax_exempt_bond_premium": box13,
            "box14_cusip_number": box14,

            # State boxes 15–17
            "state": payer_state,
            "state_id": str(random.randint(10000, 99999)),
            "state_tax_withheld": round(random.uniform(0.0, 50.0), 2),
        }

        # --- Write JSON and PDF ---
        json_path = output_dir / f"1099int_{i:03}.json"
        pdf_path = output_dir / f"1099int_{i:03}.pdf"

        with open(json_path, "w") as f:
            json.dump(record, f, indent=2)

        fill_pdf(record, pdf_path)
        print(f"[✓] Generated {pdf_path}")

    print(f"{n} synthetic 1099 forms created in {output_dir}")