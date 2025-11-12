"""Generate PDF documents for synthetic Fidelity portfolio summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from .models import PortfolioSummary


class PortfolioPDFGenerator:
    """Generate Fidelity-style PDF portfolio summaries."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles for the document."""

        # Title style
        self.styles.add(ParagraphStyle(
            name='FidelityTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#006747'),  # Fidelity green
            spaceAfter=12,
            alignment=TA_CENTER,
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='FidelitySubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#006747'),
            spaceAfter=8,
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=12,
        ))

        # Account info style
        self.styles.add(ParagraphStyle(
            name='AccountInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
        ))

    def generate_pdf(
        self,
        portfolio: PortfolioSummary,
        output_path: Path,
    ) -> None:
        """
        Generate a Fidelity-style PDF portfolio summary.

        Args:
            portfolio: PortfolioSummary object with all portfolio data
            output_path: Path where PDF should be saved
        """

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Header/Logo
        story.append(Paragraph("FIDELITY INVESTMENTS", self.styles['FidelityTitle']))
        story.append(Spacer(1, 0.2 * inch))

        # Statement title
        story.append(Paragraph("Portfolio Summary", self.styles['FidelitySubtitle']))
        story.append(Spacer(1, 0.1 * inch))

        # Account information
        story.extend(self._build_account_section(portfolio))
        story.append(Spacer(1, 0.2 * inch))

        # Portfolio summary
        story.extend(self._build_summary_section(portfolio))
        story.append(Spacer(1, 0.2 * inch))

        # Asset allocation
        story.extend(self._build_allocation_section(portfolio))
        story.append(Spacer(1, 0.2 * inch))

        # Holdings detail
        story.extend(self._build_holdings_section(portfolio))

        # Performance (if available)
        if portfolio.performance:
            story.append(Spacer(1, 0.2 * inch))
            story.extend(self._build_performance_section(portfolio))

        # Notes (if available)
        if portfolio.notes:
            story.append(Spacer(1, 0.2 * inch))
            story.extend(self._build_notes_section(portfolio))

        # Build PDF
        doc.build(story)

    def _build_account_section(self, portfolio: PortfolioSummary) -> list:
        """Build the account information section."""

        elements = []
        account = portfolio.account

        elements.append(Paragraph("Account Information", self.styles['SectionHeader']))

        account_data = [
            ['Account Name:', account.account_name],
            ['Account Number:', account.account_number],
            ['Account Type:', account.account_type],
            ['Account Owner:', account.account_owner],
            ['Statement Date:', account.statement_date],
        ]

        account_table = Table(account_data, colWidths=[2 * inch, 4 * inch])
        account_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(account_table)

        return elements

    def _build_summary_section(self, portfolio: PortfolioSummary) -> list:
        """Build the portfolio summary section."""

        elements = []

        elements.append(Paragraph("Portfolio Summary", self.styles['SectionHeader']))

        summary_data = [
            ['Total Portfolio Value:', f"${portfolio.total_portfolio_value:,.2f}"],
            ['Number of Holdings:', str(len(portfolio.holdings))],
        ]

        summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#006747')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))

        elements.append(summary_table)

        return elements

    def _build_allocation_section(self, portfolio: PortfolioSummary) -> list:
        """Build the asset allocation section."""

        elements = []
        alloc = portfolio.asset_allocation

        elements.append(Paragraph("Asset Allocation", self.styles['SectionHeader']))

        allocation_data = [
            ['Asset Class', 'Percentage'],
            ['Stocks', f"{alloc.stocks_percentage:.1f}%"],
            ['Bonds', f"{alloc.bonds_percentage:.1f}%"],
            ['Cash', f"{alloc.cash_percentage:.1f}%"],
        ]

        if alloc.other_percentage > 0:
            allocation_data.append(['Other', f"{alloc.other_percentage:.1f}%"])

        allocation_table = Table(allocation_data, colWidths=[3 * inch, 2 * inch])
        allocation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006747')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))

        elements.append(allocation_table)

        return elements

    def _build_holdings_section(self, portfolio: PortfolioSummary) -> list:
        """Build the detailed holdings section."""

        elements = []

        elements.append(Paragraph("Holdings Detail", self.styles['SectionHeader']))

        # Table header
        holdings_data = [
            ['Ticker', 'Name', 'Shares', 'Price', 'Value', 'Type']
        ]

        # Add holdings rows
        for holding in portfolio.holdings:
            holdings_data.append([
                holding.ticker,
                holding.name[:30] + '...' if len(holding.name) > 30 else holding.name,
                f"{holding.shares:.3f}",
                f"${holding.price_per_share:.2f}",
                f"${holding.total_value:,.2f}",
                holding.asset_class,
            ])

        holdings_table = Table(
            holdings_data,
            colWidths=[0.6 * inch, 2.2 * inch, 0.8 * inch, 0.8 * inch, 1.1 * inch, 0.8 * inch]
        )
        holdings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006747')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(holdings_table)

        return elements

    def _build_performance_section(self, portfolio: PortfolioSummary) -> list:
        """Build the performance metrics section."""

        elements = []
        perf = portfolio.performance

        if not perf:
            return elements

        elements.append(Paragraph("Performance", self.styles['SectionHeader']))

        perf_data = [
            ['Period', 'Return'],
        ]

        if perf.ytd_return_percentage is not None:
            perf_data.append([
                'Year-to-Date',
                f"{perf.ytd_return_percentage:+.2f}%"
            ])

        if perf.one_year_return_percentage is not None:
            perf_data.append([
                'One Year',
                f"{perf.one_year_return_percentage:+.2f}%"
            ])

        perf_table = Table(perf_data, colWidths=[3 * inch, 2 * inch])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006747')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))

        elements.append(perf_table)

        return elements

    def _build_notes_section(self, portfolio: PortfolioSummary) -> list:
        """Build the notes section."""

        elements = []

        elements.append(Paragraph("Important Information", self.styles['SectionHeader']))
        elements.append(Paragraph(portfolio.notes, self.styles['AccountInfo']))

        return elements
