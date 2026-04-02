"""Planfile integration for prollama.

Integrates planfile library (from /home/tom/github/semcod/planfile) with prollama
to provide unified GitHub task/issue management.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()

# Try to import planfile
try:
    from planfile import Planfile, quick_ticket
    from planfile.core.models import Ticket, TicketSource, TicketStatus
    from planfile.sync.github import GitHubBackend
    PLANFILE_AVAILABLE = True
except ImportError:
    PLANFILE_AVAILABLE = False
    GitHubBackend = None
    Ticket = None
    TicketSource = None
    TicketStatus = None


class PlanfileAdapter:
    """Adapter for planfile integration in prollama.
    
    Provides GitHub issue/ticket management using planfile's GitHubBackend.
    Falls back to prollama's native implementation if planfile not available.
    """
    
    def __init__(self, repo: str | None = None, token: str | None = None):
        """Initialize planfile adapter.
        
        Args:
            repo: Repository in format "owner/repo". Auto-detected if None.
            token: GitHub token. Loaded from env/credentials if None.
        """
        if not PLANFILE_AVAILABLE:
            raise ImportError(
                "planfile is required. Install with: "
                "pip install /home/tom/github/semcod/planfile"
            )
        
        self.repo = repo or self._detect_repo()
        self.token = token or self._load_token()
        self._backend: GitHubBackend | None = None
        
    def _detect_repo(self) -> str:
        """Auto-detect repo from git remote."""
        from prollama.pr import get_current_repo
        result = get_current_repo()
        if result:
            return f"{result[0]}/{result[1]}"
        raise ValueError("Could not detect repo. Are you in a git repository?")
    
    def _load_token(self) -> str:
        """Load token from prollama credentials."""
        from prollama.auth import load_github_token
        token = load_github_token()
        if token:
            return token
        # Fallback to env
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            return token
        raise ValueError("GitHub token not found. Run: prollama login")
    
    @property
    def backend(self) -> GitHubBackend:
        """Lazy-load GitHub backend."""
        if self._backend is None:
            self._backend = GitHubBackend(repo=self.repo, token=self.token)
        return self._backend
    
    def create_ticket(
        self,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        priority: str = "medium",
        assignee: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create GitHub issue via planfile.
        
        Returns dict with id, url, key, status.
        """
        import uuid
        
        # Add prollama metadata
        full_metadata = {
            "source": "prollama",
            **(metadata or {})
        }
        
        # Ensure planfile labels
        all_labels = list(labels or [])
        if "prollama" not in all_labels:
            all_labels.append("prollama")
        
        # Create Ticket object for planfile
        ticket = Ticket(
            id=str(uuid.uuid4()),
            title=title,
            description=body or "",
            labels=all_labels,
            priority=priority,
            assignee=assignee or "",
            source=TicketSource.model_validate({"tool": "github"}),
            status=TicketStatus.open,
            metadata=full_metadata,
        )
        
        # Convert to dict for backend
        ticket_dict = ticket.model_dump()
        
        # Create via planfile backend
        result = self.backend.create_ticket(ticket_dict)
        
        return {
            "id": result.id,
            "url": result.url,
            "key": result.key,
            "status": result.status,
        }
    
    def list_tickets(
        self,
        labels: list[str] | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List GitHub issues via planfile."""
        results = self.backend.list_tickets(
            labels=labels,
            status=status,
            limit=limit,
        )
        
        return [
            {
                "id": r.id,
                "status": r.status,
                "assignee": r.assignee,
                "labels": r.labels,
                "updated_at": r.updated_at,
            }
            for r in results
        ]
    
    def update_ticket(
        self,
        ticket_id: str,
        title: str | None = None,
        body: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
        assignee: str | None = None,
    ) -> None:
        """Update GitHub issue via planfile."""
        self.backend.update_ticket(
            ticket_id=ticket_id,
            title=title,
            body=body,
            status=status,
            labels=labels,
            assignee=assignee,
        )
    
    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        """Get ticket status via planfile."""
        try:
            result = self.backend.get_ticket(ticket_id)
            return {
                "id": result.id,
                "status": result.status,
                "assignee": result.assignee,
                "labels": result.labels,
                "updated_at": result.updated_at,
            }
        except Exception:
            return None


def create_prollama_ticket(
    title: str,
    description: str | None = None,
    task_type: str = "fix",
    model_used: str | None = None,
    cost: float | None = None,
    repo: str | None = None,
    token: str | None = None,
) -> dict[str, Any] | None:
    """One-liner to create GitHub issue from prollama.
    
    Args:
        title: Issue title
        description: Issue description/body
        task_type: Type of task (fix, feature, refactor, etc.)
        model_used: AI model that generated the fix
        cost: Cost of the AI generation
        repo: Repository (auto-detected if None)
        token: GitHub token (loaded from credentials if None)
    
    Returns:
        Dict with ticket info or None on failure.
    """
    if not PLANFILE_AVAILABLE:
        console.print("[yellow]⚠[/yellow] planfile not available. Skipping ticket creation.")
        return None
    
    try:
        adapter = PlanfileAdapter(repo=repo, token=token)
        
        # Build body with prollama metadata
        body = description or ""
        if model_used or cost is not None:
            body += "\n\n---\n**Prollama Metadata:**\n"
            if model_used:
                body += f"- Model: {model_used}\n"
            if cost is not None:
                body += f"- Cost: ${cost:.4f}\n"
        
        result = adapter.create_ticket(
            title=title,
            body=body,
            labels=["prollama", task_type],
            priority="medium",
            metadata={
                "tool": "prollama",
                "task_type": task_type,
                "model_used": model_used,
                "cost_usd": cost,
            },
        )
        
        console.print(f"[green]✓[/green] GitHub issue created: {result['url']}")
        return result
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create ticket: {e}")
        return None


def is_planfile_available() -> bool:
    """Check if planfile library is available."""
    return PLANFILE_AVAILABLE
