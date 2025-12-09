from agentic_user_data_processing import schemas


def test_w2_fields_defaults():
    fields = schemas.W2Fields()
    assert fields.employee_name is None
    assert fields.employer_name is None


def test_w2_fields_with_values():
    fields = schemas.W2Fields(employee_name="John Doe", employer_name="Acme Inc", wages_tips_other_comp="50000")
    assert fields.employee_name == "John Doe"
    assert fields.employer_name == "Acme Inc"


def test_form1099_fields_defaults():
    fields = schemas.Form1099Fields()
    assert fields.box1_interest_income is None


def test_portfolio_fields_defaults():
    fields = schemas.PortfolioFields()
    assert fields.total_portfolio_value is None
    assert fields.holdings == []


def test_portfolio_fields_with_holdings():
    holding = schemas.PortfolioHolding(ticker="AAPL", name="Apple Inc", shares="100", value="15000")
    fields = schemas.PortfolioFields(total_portfolio_value="15000", holdings=[holding])
    assert len(fields.holdings) == 1
    assert fields.holdings[0].ticker == "AAPL"


def test_session_context_model():
    ctx = schemas.SessionContext(session_id="test-session", user_id="test-user")
    assert ctx.session_id == "test-session"
    assert ctx.recent_messages == []


def test_auth_response_model():
    user = schemas.AuthUser(id="user-123", email="test@example.com", created_at="2024-01-01")
    assert user.id == "user-123"
    assert user.email == "test@example.com"
