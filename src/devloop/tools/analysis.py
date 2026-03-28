"""Analysis wrapper — run code2llm, vallm, redup from one place.

Usage:
    from devloop.tools.analysis import Analyzer

    a = Analyzer("./my-project")
    report = a.health()        # quick health check
    report = a.full()          # all tools combined
    print(report.cc_avg)       # 3.5
    print(report.passed)       # True if meets targets
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class HealthReport:
    """Combined analysis result from all tools."""

    project_path: str = "."
    files: int = 0
    lines: int = 0
    functions: int = 0
    classes: int = 0
    cc_avg: float = 0.0
    cc_max: int = 0
    god_modules: list[str] = field(default_factory=list)
    god_functions: list[str] = field(default_factory=list)
    vallm_pass_rate: float = 0.0
    dup_groups: int = 0
    dup_lines: int = 0
    errors: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Check if project meets quality targets."""
        return self.cc_avg <= 3.5 and self.vallm_pass_rate >= 0.90

    @property
    def grade(self) -> str:
        if self.cc_avg <= 2.5 and self.vallm_pass_rate >= 0.95:
            return "A"
        if self.cc_avg <= 3.5 and self.vallm_pass_rate >= 0.90:
            return "B"
        if self.cc_avg <= 4.5:
            return "C"
        return "D"

    def summary(self) -> str:
        lines = [
            f"Project: {self.project_path}",
            f"Grade: {self.grade} | CC\u0304={self.cc_avg:.1f} | "
            f"vallm={self.vallm_pass_rate:.0%} | "
            f"{self.files} files, {self.lines:,} LOC",
        ]
        if self.god_modules:
            lines.append(f"God modules: {', '.join(self.god_modules[:5])}")
        if self.dup_groups:
            lines.append(f"Duplications: {self.dup_groups} groups ({self.dup_lines:,} lines)")
        if self.errors:
            lines.append(f"Errors: {len(self.errors)}")
        return "\n".join(lines)


class Analyzer:
    """Unified interface for code analysis tools."""

    def __init__(self, project_path: str = "."):
        self.path = Path(project_path).resolve()

    def health(self) -> HealthReport:
        """Quick health check using code2llm."""
        report = HealthReport(project_path=str(self.path))
        report = self._run_code2llm(report)
        return report

    def full(self) -> HealthReport:
        """Full analysis: code2llm + vallm + redup."""
        report = HealthReport(project_path=str(self.path))
        report = self._run_code2llm(report)
        report = self._run_vallm(report)
        report = self._run_redup(report)
        return report

    def _run_code2llm(self, report: HealthReport) -> HealthReport:
        """Run code2llm for static analysis."""
        result = _run_cli(
            ["code2llm", str(self.path), "-f", "toon", "--json"],
            cwd=str(self.path),
        )
        if result.ok:
            report.tools_used.append("code2llm")
            data = result.json_data or {}
            report.files = data.get("files", 0)
            report.lines = data.get("lines", 0)
            report.functions = data.get("functions", 0)
            report.classes = data.get("classes", 0)
            report.cc_avg = data.get("cc_avg", 0.0)
            report.cc_max = data.get("cc_max", 0)
            report.god_modules = data.get("god_modules", [])
            report.god_functions = data.get("god_functions", [])
        elif result.error:
            report.errors.append(f"code2llm: {result.error}")
        return report

    def _run_vallm(self, report: HealthReport) -> HealthReport:
        """Run vallm for code validation."""
        result = _run_cli(
            ["vallm", "batch", str(self.path), "--recursive", "--json"],
            cwd=str(self.path),
        )
        if result.ok:
            report.tools_used.append("vallm")
            data = result.json_data or {}
            total = data.get("total", 1)
            passed = data.get("passed", 0)
            report.vallm_pass_rate = passed / max(total, 1)
        elif result.error:
            report.errors.append(f"vallm: {result.error}")
        return report

    def _run_redup(self, report: HealthReport) -> HealthReport:
        """Run redup for duplication detection."""
        result = _run_cli(
            ["redup", "scan", str(self.path), "--json"],
            cwd=str(self.path),
        )
        if result.ok:
            report.tools_used.append("redup")
            data = result.json_data or {}
            report.dup_groups = data.get("groups", 0)
            report.dup_lines = data.get("duplicate_lines", 0)
        elif result.error:
            report.errors.append(f"redup: {result.error}")
        return report


@dataclass
class CLIResult:
    ok: bool = False
    stdout: str = ""
    error: Optional[str] = None
    json_data: Optional[dict] = None


def _run_cli(cmd: list[str], cwd: str = ".") -> CLIResult:
    """Run a CLI tool and capture output."""
    import shutil

    if not shutil.which(cmd[0]):
        return CLIResult(ok=False, error=f"{cmd[0]} not found (pip install {cmd[0]})")

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        result = CLIResult(ok=proc.returncode == 0, stdout=proc.stdout)
        if proc.returncode != 0:
            result.error = proc.stderr.strip() or f"exit code {proc.returncode}"

        # Try to parse JSON output
        try:
            result.json_data = json.loads(proc.stdout)
        except (json.JSONDecodeError, ValueError):
            pass

        return result
    except subprocess.TimeoutExpired:
        return CLIResult(ok=False, error="timeout (300s)")
    except FileNotFoundError:
        return CLIResult(ok=False, error=f"{cmd[0]} not installed")
