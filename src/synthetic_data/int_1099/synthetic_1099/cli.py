# synthetic_1099/cli.py
import typer
from pathlib import Path
from .generator import generate_1099_records, DEFAULT_OUTPUT_DIR

app = typer.Typer(help="Generate synthetic 1099-INT forms.")

@app.command()
def main(
    n: int = typer.Option(1, "--n", help="Number of synthetic 1099 forms to generate."),
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
    output_dir: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", help="Directory to save generated files."),
):
    """Typer CLI entry point for synthetic 1099-INT generation."""
    generate_1099_records(n=n, seed=seed, output_dir=output_dir)

if __name__ == "__main__":
    app()
