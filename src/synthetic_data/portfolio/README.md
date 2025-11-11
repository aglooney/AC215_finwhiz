# Synthetic Portfolio Generator

Generate realistic Fidelity-style portfolio summaries for testing the FinWhiz agent service.

## Features

- **Realistic Portfolio Data**: Uses Faker and financial modeling to generate credible portfolios
- **Configurable Parameters**:
  - Portfolio size: small (<$50k), medium ($50k-$500k), large (>$500k)
  - Risk profile: conservative, moderate, aggressive
  - Random seed for reproducibility
- **Multiple Output Formats**:
  - JSON (structured data with all fields)
  - PDF (Fidelity-styled portfolio summary)

## Usage

### Generate Portfolios

```bash
# Generate 3 medium-sized moderate-risk portfolios
python -m synthetic_portfolio generate --count 3 --size medium --risk moderate

# Generate a small conservative portfolio with seed for reproducibility
python -m synthetic_portfolio generate --seed 42 --size small --risk conservative

# Generate portfolios in custom directory
python -m synthetic_portfolio generate --count 5 --output-dir ./my_portfolios
```

### Inspect Generated Portfolio

```bash
# View portfolio details in terminal
python -m synthetic_portfolio inspect outputs/portfolio_001.json
```

## Generated Portfolio Structure

Each portfolio includes:

- **Account Information**: Name, number, type, owner, statement date
- **Portfolio Summary**: Total value, number of holdings
- **Asset Allocation**: Percentage breakdown by asset class
- **Holdings Detail**: Individual positions with ticker, shares, price, value
- **Performance Metrics**: YTD and 1-year returns
- **Notes**: Additional context (optional)

## Examples

### Conservative Portfolio (Low Risk)
- 35-45% stocks
- 40-55% bonds  
- 10-20% cash
- Lower volatility holdings

### Moderate Portfolio (Medium Risk)
- 55-70% stocks
- 20-35% bonds
- 5-15% cash
- Balanced mix

### Aggressive Portfolio (High Risk)
- 75-90% stocks
- 5-15% bonds
- 2-10% cash
- Growth-oriented holdings

## Integration with FinWhiz

Generated PDFs can be uploaded to the FinWhiz agent service for testing:

```bash
# Upload to portfolio endpoint
curl -X POST http://localhost:8010/sessions/$SESSION_ID/portfolio \
  -F file=@outputs/portfolio_001.pdf
```

## Dependencies

- pydantic: Data modeling
- faker: Synthetic data generation
- reportlab: PDF generation
- typer: CLI interface
- rich: Terminal formatting

