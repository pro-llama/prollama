#!/usr/bin/env python3
"""Example: Batch anonymization of a project directory.

Scans all Python files in a directory, anonymizes each one,
and produces a privacy report.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from prollama.anonymizer import AnonymizationPipeline
from prollama.models import PrivacyLevel

console = Console()


def scan_project(directory: str, level: str = "basic") -> None:
    """Scan a project directory and report all sensitive items found."""

    project = Path(directory)
    if not project.is_dir():
        console.print(f"[red]Not a directory:[/] {directory}")
        return

    pipeline = AnonymizationPipeline(PrivacyLevel(level))
    py_files = sorted(project.rglob("*.py"))

    if not py_files:
        console.print(f"[yellow]No Python files found in {directory}[/]")
        return

    console.print(f"\n[bold]Scanning {len(py_files)} Python files in {directory}[/]")
    console.print(f"[bold]Privacy level:[/] {level}\n")

    total_stats: dict[str, int] = {}
    file_results: list[tuple[str, dict[str, int]]] = []

    for py_file in py_files:
        try:
            code = py_file.read_text(errors="replace")
            result = pipeline.run(code, language="python")

            if result.stats:
                file_results.append((str(py_file.relative_to(project)), result.stats))
                for cat, count in result.stats.items():
                    total_stats[cat] = total_stats.get(cat, 0) + count
        except Exception as e:
            console.print(f"  [yellow]⚠ Skipped {py_file}: {e}[/]")

    # Per-file results
    if file_results:
        table = Table(title="Files with Sensitive Data", show_lines=False)
        table.add_column("File", style="cyan")
        table.add_column("Findings")

        for path, stats in file_results:
            findings = ", ".join(f"{cat}: {count}" for cat, count in sorted(stats.items()))
            table.add_row(path, findings)

        console.print(table)

    # Summary
    console.print(f"\n[bold]Summary:[/]")
    console.print(f"  Files scanned: {len(py_files)}")
    console.print(f"  Files with findings: {len(file_results)}")

    if total_stats:
        console.print(f"\n[bold]Total sensitive items:[/]")
        for cat, count in sorted(total_stats.items()):
            console.print(f"  {cat}: [bold red]{count}[/]")
        total = sum(total_stats.values())
        console.print(f"\n  [bold]Total: {total} items would be anonymized[/]")
    else:
        console.print("\n  [green]✓ No sensitive data found![/]")


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    level = "basic"
    if "--level" in sys.argv:
        idx = sys.argv.index("--level")
        if idx + 1 < len(sys.argv):
            level = sys.argv[idx + 1]

    scan_project(directory, level)


if __name__ == "__main__":
    main()
