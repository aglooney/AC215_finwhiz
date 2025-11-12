"""Data models for synthetic Fidelity portfolio summaries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AccountInfo(BaseModel):
    """Account identification details."""

    account_name: str
    account_number: str
    account_type: str  # e.g., "Individual Brokerage", "IRA", "401(k)"
    account_owner: str
    statement_date: str


class Holding(BaseModel):
    """Individual security/position within a portfolio."""

    ticker: str
    name: str
    shares: float
    price_per_share: float
    total_value: float
    asset_class: str  # e.g., "Stock", "Bond", "ETF", "Mutual Fund", "Cash"
    sector: Optional[str] = None  # e.g., "Technology", "Healthcare"


class AssetAllocation(BaseModel):
    """Portfolio asset allocation breakdown."""

    stocks_percentage: float
    bonds_percentage: float
    cash_percentage: float
    other_percentage: float = 0.0

    def validate_total(self) -> bool:
        """Ensure allocations sum to ~100%."""
        total = (
            self.stocks_percentage +
            self.bonds_percentage +
            self.cash_percentage +
            self.other_percentage
        )
        return abs(total - 100.0) < 0.1


class PerformanceMetrics(BaseModel):
    """Portfolio performance data (optional, for richer statements)."""

    ytd_return_percentage: Optional[float] = None
    one_year_return_percentage: Optional[float] = None
    total_gain_loss: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Complete Fidelity portfolio summary document."""

    account: AccountInfo
    total_portfolio_value: float
    holdings: List[Holding] = Field(default_factory=list)
    asset_allocation: AssetAllocation
    performance: Optional[PerformanceMetrics] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation for downstream storage."""
        return self.model_dump()

    def calculate_totals(self) -> Dict[str, float]:
        """Calculate portfolio totals by asset class."""
        totals = {
            "stocks": 0.0,
            "bonds": 0.0,
            "cash": 0.0,
            "other": 0.0
        }

        for holding in self.holdings:
            asset_class = holding.asset_class.lower()
            if "stock" in asset_class or "equity" in asset_class:
                totals["stocks"] += holding.total_value
            elif "bond" in asset_class or "fixed" in asset_class:
                totals["bonds"] += holding.total_value
            elif "cash" in asset_class or "money market" in asset_class:
                totals["cash"] += holding.total_value
            else:
                totals["other"] += holding.total_value

        return totals
