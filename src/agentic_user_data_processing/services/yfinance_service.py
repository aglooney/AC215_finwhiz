"""
Service for fetching real-time market data using yfinance.
Follows FinWhiz service patterns with proper error handling and logging.
"""

import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging to match FinWhiz patterns
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_stock_quote(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get current quote data for a single stock.

    Returns:
        Dict with keys: ticker, price, change, change_percent, volume, market_cap, etc.
        Returns None if unable to fetch data.
    """
    try:
        logger.info(f"[get_stock_quote] Fetching quote for {ticker}")
        stock = yf.Ticker(ticker)
        info = stock.info

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        previous_close = info.get("previousClose")

        if current_price is None or previous_close is None:
            logger.warning(f"[get_stock_quote] Unable to get price data for {ticker}")
            return None

        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close != 0 else 0

        result = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": info.get("volume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "dividend_yield": info.get("dividendYield"),
            "updated_at": datetime.now().isoformat(),
        }
        logger.info(f"[get_stock_quote] Successfully fetched {ticker}: ${result['price']}")
        return result

    except Exception as e:
        logger.error(f"[get_stock_quote] Error fetching quote for {ticker}: {e}")
        return None


def get_multiple_quotes(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get quotes for multiple tickers at once.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dict mapping ticker -> quote data (only successful fetches included)
    """
    logger.info(f"[get_multiple_quotes] Fetching quotes for {len(tickers)} tickers")
    quotes = {}

    for ticker in tickers:
        quote = get_stock_quote(ticker)
        if quote:
            quotes[ticker] = quote

    logger.info(f"[get_multiple_quotes] Successfully fetched {len(quotes)}/{len(tickers)} quotes")
    return quotes


def get_portfolio_live_data(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate live portfolio metrics from holdings.
    Matches the extraction pattern from extraction_portfolio.py

    Args:
        holdings: List of holdings with keys: ticker, shares, value (original value)

    Returns:
        Dict with portfolio metrics including total value, gains/losses, holdings with live data
    """
    logger.info(f"[get_portfolio_live_data] Processing {len(holdings)} holdings")

    total_current_value = 0
    total_original_value = 0
    holdings_with_live_data = []

    for holding in holdings:
        ticker = holding.get("ticker")
        shares = holding.get("shares")
        original_value = holding.get("value")

        if not ticker or not shares:
            logger.warning("[get_portfolio_live_data] Skipping holding with missing ticker or shares")
            continue

        try:
            shares_float = float(shares)
            original_value_float = float(original_value) if original_value else 0
        except (ValueError, TypeError) as e:
            logger.warning(f"[get_portfolio_live_data] Invalid numeric data for {ticker}: {e}")
            continue

        quote = get_stock_quote(ticker)

        if quote:
            current_value = quote["price"] * shares_float
            gain_loss = current_value - original_value_float if original_value_float > 0 else 0
            gain_loss_percent = (gain_loss / original_value_float * 100) if original_value_float > 0 else 0

            holding_data = {
                "ticker": ticker,
                "name": quote["name"],
                "shares": shares_float,
                "original_value": original_value_float,
                "current_price": quote["price"],
                "current_value": round(current_value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_percent": round(gain_loss_percent, 2),
                "day_change": quote["change"],
                "day_change_percent": quote["change_percent"],
            }
            holdings_with_live_data.append(holding_data)

            total_current_value += current_value
            total_original_value += original_value_float

            logger.info(f"[get_portfolio_live_data] {ticker}: ${current_value:.2f} ({gain_loss_percent:+.2f}%)")

    total_gain_loss = total_current_value - total_original_value
    total_gain_loss_percent = (total_gain_loss / total_original_value * 100) if total_original_value > 0 else 0

    result = {
        "total_current_value": round(total_current_value, 2),
        "total_original_value": round(total_original_value, 2),
        "total_gain_loss": round(total_gain_loss, 2),
        "total_gain_loss_percent": round(total_gain_loss_percent, 2),
        "holdings": holdings_with_live_data,
        "updated_at": datetime.now().isoformat(),
    }

    logger.info(f"[get_portfolio_live_data] Total portfolio value: ${result['total_current_value']:.2f}")
    return result


def get_market_indices() -> List[Dict[str, Any]]:
    """
    Get current data for major market indices.

    Returns:
        List of index data dicts (empty list if fetch fails)
    """
    logger.info("[get_market_indices] Fetching major market indices")

    indices = {"^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ", "^RUT": "Russell 2000"}

    results = []
    for ticker, name in indices.items():
        quote = get_stock_quote(ticker)
        if quote:
            results.append({"symbol": ticker, "name": name, "price": quote["price"], "change": quote["change"], "change_percent": quote["change_percent"]})

    logger.info(f"[get_market_indices] Fetched {len(results)}/{len(indices)} indices")
    return results


def get_stock_history(ticker: str, period: str = "1mo") -> Optional[List[Dict[str, Any]]]:
    """
    Get historical price data for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        List of dicts with keys: date, open, high, low, close, volume
        Returns None if unable to fetch data
    """
    try:
        logger.info(f"[get_stock_history] Fetching {period} history for {ticker}")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            logger.warning(f"[get_stock_history] No history data found for {ticker}")
            return None

        history_data = []
        for date, row in hist.iterrows():
            history_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]),
                }
            )

        logger.info(f"[get_stock_history] Fetched {len(history_data)} data points for {ticker}")
        return history_data

    except Exception as e:
        logger.error(f"[get_stock_history] Error fetching history for {ticker}: {e}")
        return None


def get_portfolio_analytics(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate advanced portfolio analytics.

    Args:
        holdings: List of holdings with live data (output from get_portfolio_live_data)

    Returns:
        Dict with analytics metrics: top/bottom performers, risk metrics
    """
    logger.info(f"[get_portfolio_analytics] Analyzing {len(holdings)} holdings")

    if not holdings:
        return {"sector_allocation": {}, "top_performers": [], "bottom_performers": [], "risk_metrics": {}}

    # Sort by gain/loss percent
    sorted_holdings = sorted([h for h in holdings if "gain_loss_percent" in h], key=lambda x: x.get("gain_loss_percent", 0), reverse=True)

    top_performers = sorted_holdings[:5]
    bottom_performers = sorted_holdings[-5:] if len(sorted_holdings) > 5 else []

    # Calculate concentration risk
    total_value = sum(h.get("current_value", 0) for h in holdings)
    max_holding_pct = max((h.get("current_value", 0) / total_value * 100) if total_value > 0 else 0 for h in holdings) if holdings else 0

    analytics = {
        "top_performers": [
            {"ticker": h["ticker"], "name": h.get("name", h["ticker"]), "gain_loss_percent": h.get("gain_loss_percent", 0)} for h in top_performers
        ],
        "bottom_performers": [
            {"ticker": h["ticker"], "name": h.get("name", h["ticker"]), "gain_loss_percent": h.get("gain_loss_percent", 0)} for h in bottom_performers
        ],
        "risk_metrics": {
            "number_of_holdings": len(holdings),
            "largest_holding_percent": round(max_holding_pct, 2),
            "concentration_risk": "High" if max_holding_pct > 20 else "Medium" if max_holding_pct > 10 else "Low",
        },
    }

    logger.info(f"[get_portfolio_analytics] Concentration risk: {analytics['risk_metrics']['concentration_risk']}")
    return analytics
