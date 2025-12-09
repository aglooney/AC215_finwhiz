"""Tests for schemas module."""

from agentic_user_data_processing import schemas


def test_w2_fields_defaults():
    """Test W2Fields has correct default values."""
    w2 = schemas.W2Fields()
    assert w2.employee_name is None
    assert w2.employer_name is None
    assert w2.wages_tips_other_comp is None


def test_w2_fields_with_values():
    """Test W2Fields accepts provided values."""
    w2 = schemas.W2Fields(employee_name="John Doe", employer_name="Acme Corp", wages_tips_other_comp="50000")
    assert w2.employee_name == "John Doe"
    assert w2.employer_name == "Acme Corp"
    assert w2.wages_tips_other_comp == "50000"


def test_portfolio_fields_defaults():
    """Test PortfolioFields has correct default values."""
    portfolio = schemas.PortfolioFields()
    # holdings defaults to None (not [])
    assert portfolio.holdings is None
    assert portfolio.total_portfolio_value is None
    assert portfolio.account_name is None


def test_portfolio_fields_with_holdings():
    """Test PortfolioFields with holdings list."""
    holding = schemas.HoldingDetail(ticker="AAPL", name="Apple Inc", shares=100, value=15000.00)
    portfolio = schemas.PortfolioFields(total_portfolio_value=15000.00, holdings=[holding])
    assert portfolio.total_portfolio_value == 15000.00
    assert len(portfolio.holdings) == 1
    assert portfolio.holdings[0].ticker == "AAPL"


def test_holding_detail():
    """Test HoldingDetail schema."""
    holding = schemas.HoldingDetail(ticker="MSFT", name="Microsoft Corp", shares=50, value=20000.00, asset_class="Stocks")
    assert holding.ticker == "MSFT"
    assert holding.shares == 50
    assert holding.asset_class == "Stocks"


def test_session_context_defaults():
    """Test SessionContext has correct default values."""
    context = schemas.SessionContext(session_id="test-session", user_id="test-user")
    # recent_messages defaults to None (not [])
    assert context.recent_messages is None
    assert context.w2_fields is None
    assert context.portfolio_fields is None


def test_session_context_with_data():
    """Test SessionContext with nested data."""
    w2 = schemas.W2Fields(employee_name="Jane Doe")
    context = schemas.SessionContext(session_id="test-session", user_id="test-user", w2_fields=w2, summary="Test summary")
    assert context.w2_fields.employee_name == "Jane Doe"
    assert context.summary == "Test summary"


def test_form1099_fields():
    """Test Form1099Fields schema."""
    form = schemas.Form1099Fields(box1_interest_income=1234.56, state="CA")
    assert form.box1_interest_income == 1234.56
    assert form.state == "CA"


def test_auth_schemas():
    """Test authentication schemas."""
    signup = schemas.SignUpRequest(email="test@example.com", password="password123")
    assert signup.email == "test@example.com"

    signin = schemas.SignInRequest(email="test@example.com", password="password123")
    assert signin.email == "test@example.com"


def test_user_profile_update():
    """Test UserProfileUpdate schema validation."""
    profile = schemas.UserProfileUpdate(age=30, retirement_age=65, risk_tolerance="moderate", investment_goal="retirement")
    assert profile.age == 30
    assert profile.risk_tolerance == "moderate"
