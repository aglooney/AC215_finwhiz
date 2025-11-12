"""Generate realistic synthetic Fidelity portfolio summaries."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from faker import Faker

from .models import (
    AccountInfo,
    AssetAllocation,
    Holding,
    PerformanceMetrics,
    PortfolioSummary,
)

# Common stock tickers and names
STOCK_POOL = [
    ("AAPL", "Apple Inc.", "Technology"),
    ("MSFT", "Microsoft Corporation", "Technology"),
    ("GOOGL", "Alphabet Inc.", "Technology"),
    ("AMZN", "Amazon.com Inc.", "Consumer Cyclical"),
    ("NVDA", "NVIDIA Corporation", "Technology"),
    ("META", "Meta Platforms Inc.", "Technology"),
    ("TSLA", "Tesla Inc.", "Consumer Cyclical"),
    ("JPM", "JPMorgan Chase & Co.", "Financial Services"),
    ("V", "Visa Inc.", "Financial Services"),
    ("JNJ", "Johnson & Johnson", "Healthcare"),
    ("UNH", "UnitedHealth Group", "Healthcare"),
    ("PG", "Procter & Gamble", "Consumer Defensive"),
    ("HD", "Home Depot Inc.", "Consumer Cyclical"),
    ("MA", "Mastercard Inc.", "Financial Services"),
    ("DIS", "Walt Disney Company", "Communication Services"),
]

BOND_POOL = [
    ("BND", "Vanguard Total Bond Market ETF", None),
    ("AGG", "iShares Core U.S. Aggregate Bond ETF", None),
    ("BNDX", "Vanguard Total International Bond ETF", None),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", None),
    ("LQD", "iShares iBoxx Investment Grade Corporate Bond ETF", None),
]

ETF_POOL = [
    ("VTI", "Vanguard Total Stock Market ETF", None),
    ("VOO", "Vanguard S&P 500 ETF", None),
    ("QQQ", "Invesco QQQ Trust", None),
    ("VEA", "Vanguard FTSE Developed Markets ETF", None),
    ("VWO", "Vanguard FTSE Emerging Markets ETF", None),
]

ACCOUNT_TYPES = [
    "Individual Brokerage",
    "Joint Brokerage",
    "Traditional IRA",
    "Roth IRA",
    "401(k)",
    "Rollover IRA",
]


class PortfolioGenerator:
    """Generate deterministic-yet-realistic synthetic portfolio summaries."""

    def __init__(self, seed: Optional[int] = None, locale: str = "en_US"):
        self.faker = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        self.rng = random.Random(seed)

    def generate_portfolio(
        self,
        portfolio_size: str = "medium",
        risk_profile: str = "moderate",
    ) -> PortfolioSummary:
        """
        Generate a single synthetic portfolio summary.

        Args:
            portfolio_size: "small" (<$50k), "medium" ($50k-$500k), "large" (>$500k)
            risk_profile: "conservative", "moderate", "aggressive"

        Returns:
            Complete PortfolioSummary object
        """

        # Generate account info
        account = self._generate_account_info()

        # Determine portfolio value based on size
        total_value = self._generate_portfolio_value(portfolio_size)

        # Generate asset allocation based on risk profile
        asset_allocation = self._generate_asset_allocation(risk_profile)

        # Generate holdings that match the allocation
        holdings = self._generate_holdings(total_value, asset_allocation)

        # Generate performance metrics
        performance = self._generate_performance_metrics()

        # Optional notes
        notes = self._maybe_generate_notes()

        return PortfolioSummary(
            account=account,
            total_portfolio_value=round(total_value, 2),
            holdings=holdings,
            asset_allocation=asset_allocation,
            performance=performance,
            notes=notes,
        )

    def _generate_account_info(self) -> AccountInfo:
        """Generate realistic account information."""
        account_type = self.rng.choice(ACCOUNT_TYPES)
        account_number = "".join([str(self.rng.randint(0, 9)) for _ in range(9)])

        owner_name = self.faker.name()

        # Generate statement date (recent past, within last 30 days)
        days_ago = self.rng.randint(1, 30)
        statement_date = (datetime.now() - timedelta(days=days_ago)).strftime("%B %d, %Y")

        return AccountInfo(
            account_name=f"Fidelity {account_type}",
            account_number=f"Z{account_number[:4]}-{account_number[4:]}",
            account_type=account_type,
            account_owner=owner_name,
            statement_date=statement_date,
        )

    def _generate_portfolio_value(self, size: str) -> float:
        """Generate total portfolio value based on size category."""
        if size == "small":
            return self.rng.uniform(5_000, 50_000)
        elif size == "large":
            return self.rng.uniform(500_000, 2_000_000)
        else:  # medium
            return self.rng.uniform(50_000, 500_000)

    def _generate_asset_allocation(self, risk_profile: str) -> AssetAllocation:
        """Generate asset allocation percentages based on risk profile."""

        if risk_profile == "conservative":
            # Higher bonds, lower stocks
            stocks = self.rng.uniform(30, 45)
            bonds = self.rng.uniform(40, 55)
            cash = self.rng.uniform(10, 20)
        elif risk_profile == "aggressive":
            # Higher stocks, lower bonds
            stocks = self.rng.uniform(75, 90)
            bonds = self.rng.uniform(5, 15)
            cash = self.rng.uniform(2, 10)
        else:  # moderate
            stocks = self.rng.uniform(55, 70)
            bonds = self.rng.uniform(20, 35)
            cash = self.rng.uniform(5, 15)

        # Normalize to sum to 100
        total = stocks + bonds + cash
        stocks = (stocks / total) * 100
        bonds = (bonds / total) * 100
        cash = (cash / total) * 100

        return AssetAllocation(
            stocks_percentage=round(stocks, 1),
            bonds_percentage=round(bonds, 1),
            cash_percentage=round(cash, 1),
            other_percentage=0.0,
        )

    def _generate_holdings(
        self, total_value: float, allocation: AssetAllocation
    ) -> List[Holding]:
        """Generate individual holdings that match target allocation."""

        holdings: List[Holding] = []

        # Calculate target values for each asset class
        stock_target = total_value * (allocation.stocks_percentage / 100)
        bond_target = total_value * (allocation.bonds_percentage / 100)
        cash_target = total_value * (allocation.cash_percentage / 100)

        # Generate stock holdings
        holdings.extend(self._generate_asset_class_holdings(
            stock_target, STOCK_POOL + ETF_POOL, "Stock"
        ))

        # Generate bond holdings
        holdings.extend(self._generate_asset_class_holdings(
            bond_target, BOND_POOL, "Bond"
        ))

        # Generate cash holding
        if cash_target > 100:
            holdings.append(Holding(
                ticker="SPAXX",
                name="Fidelity Government Money Market Fund",
                shares=round(cash_target, 2),
                price_per_share=1.00,
                total_value=round(cash_target, 2),
                asset_class="Cash",
                sector=None,
            ))

        return holdings

    def _generate_asset_class_holdings(
        self, target_value: float, pool: List[tuple], asset_class: str
    ) -> List[Holding]:
        """Generate holdings for a specific asset class."""

        if target_value < 100:
            return []

        holdings: List[Holding] = []

        # Determine number of holdings (3-8 for diversification)
        num_holdings = min(self.rng.randint(3, 8), len(pool))
        selected = self.rng.sample(pool, num_holdings)

        remaining_value = target_value

        for i, (ticker, name, sector) in enumerate(selected):
            # Last holding gets remaining value
            if i == len(selected) - 1:
                holding_value = remaining_value
            else:
                # Allocate 10-40% of remaining value
                allocation_pct = self.rng.uniform(0.10, 0.40)
                holding_value = remaining_value * allocation_pct
                remaining_value -= holding_value

            # Generate realistic price and shares
            price = self._generate_realistic_price(asset_class)
            shares = holding_value / price

            holdings.append(Holding(
                ticker=ticker,
                name=name,
                shares=round(shares, 3),
                price_per_share=round(price, 2),
                total_value=round(shares * price, 2),
                asset_class=asset_class,
                sector=sector,
            ))

        return holdings

    def _generate_realistic_price(self, asset_class: str) -> float:
        """Generate realistic price per share based on asset class."""

        if asset_class == "Cash":
            return 1.00
        elif asset_class == "Bond":
            # Bond ETFs typically $50-$120
            return self.rng.uniform(50, 120)
        else:  # Stocks/ETFs
            # More variation in stock prices
            return self.rng.choice([
                self.rng.uniform(10, 50),    # Low-priced stocks
                self.rng.uniform(50, 200),   # Mid-priced stocks
                self.rng.uniform(200, 500),  # High-priced stocks
            ])

    def _generate_performance_metrics(self) -> PerformanceMetrics:
        """Generate realistic performance metrics."""

        # YTD return: -20% to +40%
        ytd = self.rng.uniform(-20, 40)

        # One year return: -15% to +35%
        one_year = self.rng.uniform(-15, 35)

        return PerformanceMetrics(
            ytd_return_percentage=round(ytd, 2),
            one_year_return_percentage=round(one_year, 2),
            total_gain_loss=None,  # Can be calculated from returns
        )

    def _maybe_generate_notes(self) -> Optional[str]:
        """Occasionally generate notes/commentary."""

        if self.rng.random() < 0.3:  # 30% chance of notes
            notes_options = [
                "Portfolio rebalanced on statement date to maintain target allocation.",
                "Dividend reinvestment active for all eligible securities.",
                "This statement includes all activity through the close of business on the statement date.",
                "Market values reflect closing prices as of the statement date.",
            ]
            return self.rng.choice(notes_options)

        return None
