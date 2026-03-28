"""Tickets wrapper — manage planfile tickets without the ceremony.

Usage:
    from devloop.tools.tickets import Tickets

    t = Tickets("./my-project")
    t.add("Fix god module in cli.py", priority="high")
    t.from_analysis(report)    # auto-create tickets from analysis
    t.list()                   # show current sprint
    t.sync()                   # push to GitHub/Jira
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from devloop.config import TicketConfig


@dataclass
class Ticket:
    """A single work item."""

    id: str = ""
    title: str = ""
    description: str = ""
    priority: str = "normal"  # low | normal | high | critical
    status: str = "open"  # open | in_progress | review | done | blocked
    type: str = "task"  # task | bug | refactor | feature | test
    sprint: str = "current"
    source: str = "human"  # human | code2llm | vallm | redup | llx
    created: str = ""
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "type": self.type,
            "sprint": self.sprint,
            "source": self.source,
            "created": self.created or datetime.now().isoformat(),
            "tags": self.tags,
            "meta": self.meta,
        }


class Tickets:
    """Manage project tickets via planfile or local YAML."""

    def __init__(self, project_path: str = ".", config: Optional[TicketConfig] = None):
        self.path = Path(project_path).resolve()
        self.config = config or TicketConfig.from_env()
        self._store_path = self.path / ".devloop" / "tickets.yaml"
        self._counter = 0
        self._tickets: list[Ticket] = []
        self._load()

    def add(
        self,
        title: str,
        *,
        description: str = "",
        priority: str = "normal",
        type: str = "task",
        source: str = "human",
        tags: Optional[list[str]] = None,
        meta: Optional[dict] = None,
    ) -> Ticket:
        """Create a new ticket."""
        self._counter += 1
        ticket = Ticket(
            id=f"DLP-{self._counter:04d}",
            title=title,
            description=description,
            priority=priority,
            type=type,
            source=source,
            tags=tags or [],
            meta=meta or {},
            created=datetime.now().isoformat(),
        )
        self._tickets.append(ticket)
        self._save()

        # Also try planfile CLI if available
        self._planfile_add(ticket)

        return ticket

    def from_analysis(self, report) -> list[Ticket]:
        """Auto-generate tickets from a HealthReport."""
        created = []

        for mod in getattr(report, "god_modules", []):
            t = self.add(
                f"Refactor god module: {mod}",
                type="refactor",
                priority="high",
                source="code2llm",
                tags=["god-module", "tech-debt"],
            )
            created.append(t)

        for func in getattr(report, "god_functions", [])[:10]:
            t = self.add(
                f"Split god function: {func}",
                type="refactor",
                priority="normal",
                source="code2llm",
                tags=["god-function", "complexity"],
            )
            created.append(t)

        if getattr(report, "dup_groups", 0) > 0:
            t = self.add(
                f"Remove {report.dup_groups} duplication groups "
                f"({report.dup_lines:,} lines)",
                type="refactor",
                priority="normal",
                source="redup",
                tags=["duplication"],
            )
            created.append(t)

        pass_rate = getattr(report, "vallm_pass_rate", 1.0)
        if pass_rate < 0.90:
            t = self.add(
                f"Fix validation failures (pass rate: {pass_rate:.0%})",
                type="bug",
                priority="high",
                source="vallm",
                tags=["validation"],
            )
            created.append(t)

        return created

    def list(self, status: Optional[str] = None) -> list[Ticket]:
        """List tickets, optionally filtered by status."""
        if status:
            return [t for t in self._tickets if t.status == status]
        return list(self._tickets)

    def update(self, ticket_id: str, **kwargs) -> Optional[Ticket]:
        """Update a ticket by ID."""
        for ticket in self._tickets:
            if ticket.id == ticket_id:
                for key, value in kwargs.items():
                    if hasattr(ticket, key):
                        setattr(ticket, key, value)
                self._save()
                return ticket
        return None

    def sync(self) -> dict:
        """Sync tickets to external backend (GitHub, Jira, etc.)."""
        if self.config.backend == "local":
            return {"synced": 0, "backend": "local (no sync needed)"}

        try:
            result = subprocess.run(
                ["planfile", "sync", self.config.backend, "--push"],
                cwd=str(self.path),
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "synced": True,
                "backend": self.config.backend,
                "output": result.stdout.strip(),
            }
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return {"synced": False, "error": str(e)}

    def board(self) -> dict[str, list[Ticket]]:
        """Kanban-style board view."""
        board: dict[str, list[Ticket]] = {
            "open": [],
            "in_progress": [],
            "review": [],
            "done": [],
            "blocked": [],
        }
        for t in self._tickets:
            board.setdefault(t.status, []).append(t)
        return board

    def _load(self):
        """Load tickets from local store."""
        if self._store_path.exists():
            try:
                data = yaml.safe_load(self._store_path.read_text()) or {}
                self._counter = data.get("counter", 0)
                for td in data.get("tickets", []):
                    self._tickets.append(Ticket(**td))
            except Exception:
                pass

    def _save(self):
        """Save tickets to local store."""
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "counter": self._counter,
            "tickets": [t.to_dict() for t in self._tickets],
        }
        self._store_path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False)
        )

    def _planfile_add(self, ticket: Ticket):
        """Try to also add via planfile CLI."""
        import shutil

        if not shutil.which("planfile"):
            return
        try:
            subprocess.run(
                [
                    "planfile",
                    "ticket",
                    "add",
                    ticket.title,
                    "--priority",
                    ticket.priority,
                    "--type",
                    ticket.type,
                ],
                cwd=str(self.path),
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass
