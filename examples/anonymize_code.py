#!/usr/bin/env python3
"""Example: Anonymize source code using prollama's three-layer pipeline.

Usage:
    python examples/anonymize_code.py [file_path] [--level basic|full]
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prollama.anonymizer import AnonymizationPipeline
from prollama.models import PrivacyLevel

console = Console()


def anonymize_and_compare(file_path: str, level: str = "full") -> None:
    """Anonymize a file and display a comparison of original vs anonymized."""

    code = Path(file_path).read_text()
    privacy_level = PrivacyLevel(level)

    console.print(f"\n[bold]Anonymizing:[/] {file_path}")
    console.print(f"[bold]Level:[/] {privacy_level.value}\n")

    # Run pipeline
    pipeline = AnonymizationPipeline(privacy_level)
    result = pipeline.run(code, language="python")

    # Display stats
    if result.stats:
        table = Table(title="Anonymization Results", show_lines=False)
        table.add_column("Category", style="cyan")
        table.add_column("Items Found", style="bold")
        for category, count in sorted(result.stats.items()):
            table.add_row(category, str(count))
        console.print(table)

    # Display anonymized code
    console.print(Panel(
        result.anonymized_code,
        title="Anonymized Output",
        border_style="blue",
    ))

    # Show mappings
    if result.mappings:
        console.print(f"\n[bold]Mappings ({len(result.mappings)} total):[/]\n")
        for m in result.mappings:
            original_display = m.original[:50] + "…" if len(m.original) > 50 else m.original
            console.print(f"  [cyan]{m.replacement:20s}[/] ← [dim]{original_display}[/]  ({m.category})")

    # Verify rehydration
    restored = pipeline.rehydrate(result.anonymized_code, result.mappings)
    if restored == code:
        console.print("\n[green]✓ Rehydration verified — original code perfectly restored[/]")
    else:
        console.print("\n[red]✗ Rehydration mismatch — some content was not restored[/]")


def main():
    if len(sys.argv) < 2:
        # Default: use the bundled fintech example
        default = Path(__file__).parent / "sample_code" / "fintech_app.py"
        if default.exists():
            file_path = str(default)
        else:
            console.print("[red]Usage:[/] python anonymize_code.py <file_path> [--level basic|full]")
            sys.exit(1)
    else:
        file_path = sys.argv[1]

    level = "full"
    if "--level" in sys.argv:
        idx = sys.argv.index("--level")
        if idx + 1 < len(sys.argv):
            level = sys.argv[idx + 1]

    anonymize_and_compare(file_path, level)


if __name__ == "__main__":
    main()
