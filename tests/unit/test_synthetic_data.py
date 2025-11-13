from synthetic_data.w2.synthetic_w2.generator import W2RecordGenerator
from synthetic_data.w2.synthetic_w2.models import W2Record


def test_w2_generator_is_reproducible():
    gen_a = W2RecordGenerator(seed=42)
    gen_b = W2RecordGenerator(seed=42)

    rec_a = gen_a.build_record()
    rec_b = gen_b.build_record()

    assert isinstance(rec_a, W2Record)
    assert rec_a.model_dump() == rec_b.model_dump()
    assert rec_a.tax_year == 2025
    assert rec_a.employee.first_name
    assert rec_a.employer.ein
    assert rec_a.box1_wages > 0
    assert rec_a.box2_federal_income_tax_withheld > 0
    assert rec_a.state_local


def test_w2_generator_optional_fields_within_bounds():
    gen = W2RecordGenerator(seed=7)
    record = gen.build_record()

    assert 45_000 <= record.box1_wages <= 195_000
    assert record.box6_medicare_tax_withheld >= 0
    assert all(entry.amount >= 0 for entry in record.box12)
    assert all(entry.state_income_tax >= 0 for entry in record.state_local)
