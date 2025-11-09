"""CLI interface for generating synthetic portfolio summaries."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .generator import PortfolioGenerator
from .pdf_generator import PortfolioPDFGenerator

app = typer.Typer(help="Generate synthetic Fidelity portfolio summaries")
console = Console()


@app.command()
def generate(
    count: int = typer.Option(1, "--count", "-n", help="Number of portfolios to generate"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility"),
    output_dir: Path = typer.Option(
        Path("outputs"),
        "--output-dir",
        "-o",
        help="Output directory for generated files",
    ),
    size: str = typer.Option(
        "medium",
        "--size",
        help="Portfolio size: small (<$50k), medium ($50k-$500k), large (>$500k)",
    ),
    risk: str = typer.Option(
        "moderate",
        "--risk",
        help="Risk profile: conservative, moderate, aggressive",
    ),
) -> None:
    """Generate synthetic Fidelity portfolio summary documents."""
    
    # Validate inputs
    if size not in ["small", "medium", "large"]:
        console.print("[red]Error: size must be 'small', 'medium', or 'large'[/red]")
        raise typer.Exit(1)
    
    if risk not in ["conservative", "moderate", "aggressive"]:
        console.print("[red]Error: risk must be 'conservative', 'moderate', or 'aggressive'[/red]")
        raise typer.Exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize generators
    portfolio_gen = PortfolioGenerator(seed=seed)
    pdf_gen = PortfolioPDFGenerator()
    
    console.print(f"\n[bold green]Generating {count} portfolio(s)...[/bold green]\n")
    console.print(f"  Size: {size}")
    console.print(f"  Risk Profile: {risk}")
    console.print(f"  Output: {output_dir}\n")
    
    for i in range(count):
        # Generate portfolio data
        portfolio = portfolio_gen.generate_portfolio(
            portfolio_size=size,
            risk_profile=risk,
        )
        
        # File naming
        file_base = f"portfolio_{i+1:03d}"
        json_path = output_dir / f"{file_base}.json"
        pdf_path = output_dir / f"{file_base}.pdf"
        
        # Save JSON
        with open(json_path, "w") as f:
            json.dump(portfolio.to_dict(), f, indent=2)
        
        # Generate PDF
        pdf_gen.generate_pdf(portfolio, pdf_path)
        
        # Display summary
        console.print(f"[green]✓[/green] Generated portfolio {i+1}/{count}")
        console.print(f"    Account: {portfolio.account.account_number}")
        console.print(f"    Value: ${portfolio.total_portfolio_value:,.2f}")
        console.print(f"    Holdings: {len(portfolio.holdings)}")
        console.print(f"    JSON: {json_path}")
        console.print(f"    PDF: {pdf_path}\n")
    
    console.print(f"[bold green]✓ Successfully generated {count} portfolio(s)![/bold green]\n")


@app.command()
def inspect(
    json_file: Path = typer.Argument(..., help="Path to portfolio JSON file"),
) -> None:
    """Inspect a generated portfolio JSON file."""
    
    if not json_file.exists():
        console.print(f"[red]Error: File not found: {json_file}[/red]")
        raise typer.Exit(1)
    
    # Load portfolio
    with open(json_file) as f:
        data = json.load(f)
    
    # Display account info
    console.print("\n[bold]Account Information[/bold]")
    account = data["account"]
    for key, value in account.items():
        console.print(f"  {key}: {value}")
    
    # Display portfolio summary
    console.print(f"\n[bold]Portfolio Summary[/bold]")
    console.print(f"  Total Value: ${data['total_portfolio_value']:,.2f}")
    console.print(f"  Number of Holdings: {len(data['holdings'])}")
    
    # Display asset allocation
    console.print(f"\n[bold]Asset Allocation[/bold]")
    alloc = data["asset_allocation"]
    console.print(f"  Stocks: {alloc['stocks_percentage']:.1f}%")
    console.print(f"  Bonds: {alloc['bonds_percentage']:.1f}%")
    console.print(f"  Cash: {alloc['cash_percentage']:.1f}%")
    
    # Display holdings table
    console.print(f"\n[bold]Holdings[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Ticker", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Shares", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Value", justify="right", style="yellow")
    table.add_column("Type")
    
    for holding in data["holdings"]:
        table.add_row(
            holding["ticker"],
            holding["name"][:30] + "..." if len(holding["name"]) > 30 else holding["name"],
            f"{holding['shares']:.3f}",
            f"${holding['price_per_share']:.2f}",
            f"${holding['total_value']:,.2f}",
            holding["asset_class"],
        )
    
    console.print(table)
    
    # Display performance if available
    if data.get("performance"):
        console.print(f"\n[bold]Performance[/bold]")
        perf = data["performance"]
        if perf.get("ytd_return_percentage") is not None:
            console.print(f"  YTD Return: {perf['ytd_return_percentage']:+.2f}%")
        if perf.get("one_year_return_percentage") is not None:
            console.print(f"  1-Year Return: {perf['one_year_return_percentage']:+.2f}%")
    
    console.print("\n")


if __name__ == "__main__":
    app()

