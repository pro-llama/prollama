"""Pipeline — for users who want custom workflows.

Usage:
    from devloop import Pipeline

    result = (
        Pipeline("./my-app")
        .analyze()
        .create_tickets()
        .execute(max_tickets=5)
        .validate()
        .sync("github")
        .report()
    )
"""

from __future__ import annotations

from typing import Optional

from devloop.project import Project
from devloop.config import Config


class Pipeline:
    """Composable workflow: chain steps fluently."""

    def __init__(self, path: str = ".", config: Optional[Config] = None):
        self.project = Project(path, config)
        self._steps: list[dict] = []
        self._results: dict = {}

    def analyze(self, full: bool = True) -> Pipeline:
        """Step: analyze project health."""
        report = self.project.analyze(full=full)
        self._results["analysis"] = report
        self._steps.append({"step": "analyze", "grade": report.grade})
        return self

    def create_tickets(self) -> Pipeline:
        """Step: auto-create tickets from analysis."""
        report = self._results.get("analysis")
        if not report:
            report = self.project.analyze()
            self._results["analysis"] = report

        tickets = self.project._tickets.from_analysis(report)
        self._results["tickets_created"] = tickets
        self._steps.append({"step": "create_tickets", "count": len(tickets)})
        return self

    def execute(self, max_tickets: int = 10) -> Pipeline:
        """Step: execute open tickets via LLM."""
        result = self.project.execute()
        self._results["execution"] = result
        self._steps.append({"step": "execute", "count": result["executed"]})
        return self

    def validate(self) -> Pipeline:
        """Step: re-analyze to check improvements."""
        report = self.project.analyze(full=True)
        self._results["validation"] = report
        prev = self._results.get("analysis")
        improved = prev and report.cc_avg < prev.cc_avg
        self._steps.append({
            "step": "validate",
            "grade": report.grade,
            "improved": improved,
        })
        return self

    def sync(self, backend: Optional[str] = None) -> Pipeline:
        """Step: sync tickets to external system."""
        if backend:
            self.project.config.tickets.backend = backend
        result = self.project.sync()
        self._results["sync"] = result
        self._steps.append({"step": "sync", "backend": backend or "local"})
        return self

    def report(self) -> dict:
        """Get pipeline results."""
        return {
            "project": str(self.project.path),
            "steps": self._steps,
            "results": {
                k: (v.summary() if hasattr(v, "summary") else v)
                for k, v in self._results.items()
            },
        }
