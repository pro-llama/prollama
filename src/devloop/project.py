"""Project — the single object you need to know.

Expanded from wronai with:
- Progressive algorithmization (Loop)
- Propact workflow execution
- Planfile-aware proxy headers (X-Planfile-Ref, X-Workflow-Ref)
- Per-ticket cost ledger
- DSL rule extraction

Usage:
    from devloop import Project

    p = Project("./my-app")
    p.analyze()                     # code2llm + vallm + redup
    p.plan(sprints=2)               # generate strategy → tickets
    p.execute()                     # llx picks model, proxym routes
    p.run_workflow("refactor.md")   # execute Propact workflow
    p.algo.discover()               # start progressive algorithmization
    p.status()                      # health + tickets + budget + algo progress
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devloop.config import Config
from devloop.tools.analysis import Analyzer, HealthReport
from devloop.tools.tickets import Tickets, Ticket
from devloop.algo import Loop


class Project:
    """One project, all tools, zero boilerplate."""

    def __init__(self, path: str = ".", config: Optional[Config] = None):
        self.path = Path(path).resolve()
        self.config = config or Config.load()
        self.config.project_path = str(self.path)

        self._analyzer = Analyzer(str(self.path))
        self._tickets = Tickets(str(self.path), self.config.tickets)
        self._last_report: Optional[HealthReport] = None

        # New: progressive algorithmization loop
        self.algo = Loop(str(self.path))

    # ── Core workflow ─────────────────────────────────────

    def analyze(self, full: bool = True) -> HealthReport:
        """Analyze project health."""
        if full:
            self._last_report = self._analyzer.full()
        else:
            self._last_report = self._analyzer.health()
        return self._last_report

    def plan(
        self,
        sprints: int = 2,
        focus: str = "complexity",
        auto_tickets: bool = True,
    ) -> dict:
        """Generate a sprint plan from analysis results."""
        if not self._last_report:
            self._last_report = self.analyze()

        tickets_created = []
        if auto_tickets:
            tickets_created = self._tickets.from_analysis(self._last_report)

        plan = {
            "project": str(self.path),
            "grade": self._last_report.grade,
            "sprints_planned": sprints,
            "focus": focus,
            "tickets_created": len(tickets_created),
            "summary": self._last_report.summary(),
            "tickets": [t.to_dict() for t in tickets_created],
        }

        plan["strategy"] = self._generate_strategy(sprints, focus)
        return plan

    def execute(self, ticket_id: Optional[str] = None) -> dict:
        """Execute work with planfile-aware headers and cost tracking."""
        from devloop.tools.proxy import Proxy

        results = []
        proxy = Proxy(self.config.proxy)

        tickets_to_run = (
            [t for t in self._tickets.list() if t.id == ticket_id]
            if ticket_id
            else self._tickets.list(status="open")
        )

        for ticket in tickets_to_run[:10]:
            self._tickets.update(ticket.id, status="in_progress")

            prompt = self._build_prompt(ticket)
            tier = self._select_tier(ticket)

            # Planfile-aware headers
            response = proxy.ask(
                prompt,
                tier=tier,
                context=True,
                planfile_ref=f"{self.path.name}/current/{ticket.id}",
            )

            # Track cost per ticket
            if "[proxy error" not in response.content:
                cost_meta = {
                    "model": response.model,
                    "cost_usd": response.cost_usd,
                    "elapsed_ms": response.elapsed_ms,
                    "tier": response.tier,
                }
                self._tickets.update(ticket.id, status="review", meta=cost_meta)

                # Feed trace to algo loop
                self.algo.add_trace(
                    prompt=prompt,
                    response=response.content,
                    **cost_meta,
                )

                results.append({
                    "ticket": ticket.id,
                    "status": "review",
                    **cost_meta,
                })
            else:
                self._tickets.update(ticket.id, status="blocked")
                results.append({
                    "ticket": ticket.id,
                    "status": "blocked",
                    "error": response.content,
                })

        proxy.close()
        return {"executed": len(results), "results": results}

    def status(self) -> dict:
        """Full project status: health + tickets + budget + algo progress."""
        from devloop.tools.proxy import Proxy
        from devloop.tools import discover_tools

        report = self._last_report or self.analyze(full=False)
        board = self._tickets.board()

        proxy = Proxy(self.config.proxy)
        budget = proxy.budget()
        proxy_healthy = proxy.health()
        proxy.close()

        tools = discover_tools()
        algo_report = self.algo.report()

        # Cost ledger
        total_cost = sum(
            t.meta.get("cost_usd", 0) for t in self._tickets.list() if t.meta
        )

        return {
            "project": str(self.path),
            "health": {
                "grade": report.grade,
                "cc_avg": report.cc_avg,
                "vallm_pass_rate": report.vallm_pass_rate,
                "files": report.files,
                "lines": report.lines,
            },
            "tickets": {
                "open": len(board.get("open", [])),
                "in_progress": len(board.get("in_progress", [])),
                "review": len(board.get("review", [])),
                "done": len(board.get("done", [])),
                "blocked": len(board.get("blocked", [])),
            },
            "cost_ledger": {
                "total_spent_usd": total_cost,
                "budget_remaining": budget,
            },
            "algo": algo_report,
            "proxy": {"healthy": proxy_healthy},
            "tools": {name: str(s) for name, s in tools.items()},
        }

    # ── Propact workflows ─────────────────────────────────

    def run_workflow(self, workflow_path: str, *, dry_run: bool = False) -> dict:
        """Execute a Propact Markdown workflow."""
        from devloop.propact import Workflow

        wf = Workflow(workflow_path)
        errors = wf.validate()
        if errors:
            return {"success": False, "errors": errors}

        result = wf.execute(dry_run=dry_run, proxy_url=self.config.proxy.url)

        # Create tickets for failed steps
        for step in result.steps:
            if step.status == "failed":
                self._tickets.add(
                    f"Workflow step failed: {step.title}",
                    description=step.result[:500],
                    priority="high",
                    type="bug",
                    source="propact",
                    tags=["workflow", workflow_path],
                )

        return {
            "success": result.success,
            "title": result.title,
            "steps_done": result.steps_done,
            "steps_failed": result.steps_failed,
            "total_cost_usd": result.total_cost_usd,
            "elapsed_ms": result.total_elapsed_ms,
        }

    # ── Convenience shortcuts ─────────────────────────────

    def ask(self, prompt: str, **kwargs) -> str:
        """Quick LLM query with planfile-aware routing."""
        from devloop.tools.proxy import Proxy

        with Proxy(self.config.proxy) as proxy:
            resp = proxy.ask(prompt, **kwargs)
            # Feed to algo loop
            self.algo.add_trace(
                prompt=prompt,
                response=resp.content,
                model=resp.model,
                cost_usd=resp.cost_usd,
            )
            return resp.content

    def add_ticket(self, title: str, **kwargs) -> Ticket:
        return self._tickets.add(title, **kwargs)

    def sync(self) -> dict:
        return self._tickets.sync()

    # ── Private helpers ───────────────────────────────────

    def _build_prompt(self, ticket: Ticket) -> str:
        return (
            f"Task: {ticket.title}\n"
            f"Type: {ticket.type}\n"
            f"Priority: {ticket.priority}\n"
            f"Description: {ticket.description or 'See title'}\n"
            f"Project: {self.path.name}\n"
            f"Instructions: Provide a concrete solution."
        )

    def _select_tier(self, ticket: Ticket) -> str:
        mapping = {
            "critical": "deep",
            "high": "complex",
            "normal": "standard",
            "low": "cheap",
        }
        return mapping.get(ticket.priority, "standard")

    def _generate_strategy(self, sprints: int, focus: str) -> Optional[dict]:
        import shutil, subprocess, json
        if not shutil.which("planfile"):
            return None
        try:
            result = subprocess.run(
                ["planfile", "strategy", "generate", str(self.path),
                 "--sprints", str(sprints), "--focus", focus, "--json"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None
