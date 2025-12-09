import pytest
from unittest.mock import patch, MagicMock
from agentic_user_data_processing.services import yfinance_service


@pytest.fixture
def mock_yf_ticker():
    with patch("agentic_user_data_processing.services.yfinance_service.yf.Ticker") as mock:
        yield mock


def test_get_stock_quote_success(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "currentPrice": 150.0,
        "previousClose": 148.0,
        "longName": "Apple Inc.",
        "volume": 1000000,
        "marketCap": 2000000000000,
    }
    mock_yf_ticker.return_value = mock_ticker

    result = yfinance_service.get_stock_quote("AAPL")

    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["price"] == 150.0
    assert result["change"] == 2.0
    assert result["change_percent"] == pytest.approx(1.35, rel=0.1)


def test_get_stock_quote_missing_price(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_ticker.info = {}
    mock_yf_ticker.return_value = mock_ticker

    result = yfinance_service.get_stock_quote("INVALID")
    assert result is None


def test_get_stock_quote_exception(mock_yf_ticker):
    mock_yf_ticker.side_effect = Exception("API Error")

    result = yfinance_service.get_stock_quote("AAPL")
    assert result is None


def test_get_multiple_quotes(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "currentPrice": 100.0,
        "previousClose": 99.0,
        "longName": "Test Stock",
    }
    mock_yf_ticker.return_value = mock_ticker

    result = yfinance_service.get_multiple_quotes(["AAPL", "GOOGL"])
    assert len(result) == 2


def test_get_portfolio_live_data_with_valid_holdings(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "currentPrice": 150.0,
        "previousClose": 148.0,
        "longName": "Apple Inc.",
    }
    mock_yf_ticker.return_value = mock_ticker

    holdings = [{"ticker": "AAPL", "shares": "10", "value": "1400", "name": "Apple Inc."}]

    result = yfinance_service.get_portfolio_live_data(holdings)

    assert result["total_current_value"] == 1500.0
    assert result["total_original_value"] == 1400.0
    assert len(result["holdings"]) == 1


def test_get_portfolio_live_data_money_market_fund():
    holdings = [{"ticker": "SPAXX", "shares": "1000", "value": "1000", "name": "Fidelity Money Market"}]

    with patch.object(yfinance_service, "get_stock_quote", return_value=None):
        result = yfinance_service.get_portfolio_live_data(holdings)

    assert len(result["holdings"]) == 1
    assert result["holdings"][0]["current_price"] == 1.00
    assert result["holdings"][0]["ticker"] == "SPAXX"


def test_get_portfolio_live_data_unknown_ticker_fallback():
    holdings = [{"ticker": "UNKNOWN", "shares": "100", "value": "5000", "name": "Unknown Stock"}]

    with patch.object(yfinance_service, "get_stock_quote", return_value=None):
        result = yfinance_service.get_portfolio_live_data(holdings)

    assert len(result["holdings"]) == 1
    assert result["holdings"][0]["current_price"] == 50.0  # 5000/100


def test_get_portfolio_live_data_missing_ticker():
    holdings = [{"shares": "10", "value": "100"}]  # Missing ticker

    result = yfinance_service.get_portfolio_live_data(holdings)
    assert len(result["holdings"]) == 0


def test_get_portfolio_live_data_invalid_shares():
    holdings = [{"ticker": "AAPL", "shares": "invalid", "value": "100"}]

    result = yfinance_service.get_portfolio_live_data(holdings)
    assert len(result["holdings"]) == 0


def test_get_market_indices(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "currentPrice": 4500.0,
        "previousClose": 4480.0,
        "longName": "S&P 500",
    }
    mock_yf_ticker.return_value = mock_ticker

    result = yfinance_service.get_market_indices()
    assert len(result) == 4  # S&P 500, Dow, NASDAQ, Russell


def test_get_stock_history_success(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_hist = MagicMock()
    mock_hist.empty = False
    mock_hist.iterrows.return_value = [(MagicMock(strftime=lambda x: "2024-01-01"), {"Open": 100, "High": 105, "Low": 99, "Close": 103, "Volume": 1000000})]
    mock_ticker.history.return_value = mock_hist
    mock_yf_ticker.return_value = mock_ticker

    result = yfinance_service.get_stock_history("AAPL", "1mo")
    assert result is not None


def test_get_stock_history_empty(mock_yf_ticker):
    mock_ticker = MagicMock()
    mock_hist = MagicMock()
    mock_hist.empty = True
    mock_ticker.history.return_value = mock_hist
    mock_yf_ticker.return_value = mock_ticker

    result = yfinance_service.get_stock_history("INVALID")
    assert result is None


def test_get_portfolio_analytics():
    holdings = [
        {"ticker": "AAPL", "current_value": 1000, "gain_loss_percent": 10},
        {"ticker": "GOOGL", "current_value": 2000, "gain_loss_percent": -5},
        {"ticker": "MSFT", "current_value": 500, "gain_loss_percent": 15},
    ]

    result = yfinance_service.get_portfolio_analytics(holdings)

    assert "top_performers" in result
    assert "bottom_performers" in result
    assert "risk_metrics" in result
    assert result["risk_metrics"]["number_of_holdings"] == 3


def test_get_portfolio_analytics_empty():
    result = yfinance_service.get_portfolio_analytics([])
    assert result["top_performers"] == []
    assert result["bottom_performers"] == []
