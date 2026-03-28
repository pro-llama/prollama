"""
Ticket management for Prollama
"""

from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class Ticket(BaseModel):
    """Ticket model for issue tracking"""
    id: int = Field(..., description="Ticket ID")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    status: str = Field(default="open", description="Ticket status")
    priority: str = Field(default="medium", description="Ticket priority")
    assignee: Optional[str] = Field(default=None, description="Ticket assignee")
    labels: List[str] = Field(default_factory=list, description="Ticket labels")


class TicketCreate(BaseModel):
    """Ticket creation model"""
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    labels: List[str] = Field(default_factory=list, description="Ticket labels")
    priority: str = Field(default="medium", description="Ticket priority")


class TicketManager:
    """Manager for ticket operations across different providers"""
    
    def __init__(self, provider: str = "github", token: Optional[str] = None, repo: Optional[str] = None):
        self.provider = provider
        self.token = token
        self.repo = repo
        self.client = httpx.Client()
    
    def create_ticket(self, ticket: TicketCreate) -> Ticket:
        """Create a new ticket"""
        if self.provider == "github":
            return self._github_create_ticket(ticket)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _github_create_ticket(self, ticket: TicketCreate) -> Ticket:
        """Create GitHub issue"""
        if not self.token or not self.repo:
            raise ValueError("GitHub token and repo are required")
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        data = {
            "title": ticket.title,
            "body": ticket.description,
            "labels": ticket.labels
        }
        
        try:
            response = self.client.post(
                f"https://api.github.com/repos/{self.repo}/issues",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            return Ticket(
                id=result["number"],
                title=result["title"],
                description=result["body"] or "",
                status=result["state"],
                labels=[label["name"] for label in result.get("labels", [])],
                assignee=result.get("assignee", {}).get("login") if result.get("assignee") else None
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create GitHub issue: {e}")
            raise
    
    def list_tickets(self, status: str = "open") -> List[Ticket]:
        """List tickets"""
        if self.provider == "github":
            return self._github_list_tickets(status)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _github_list_tickets(self, status: str) -> List[Ticket]:
        """List GitHub issues"""
        if not self.token or not self.repo:
            raise ValueError("GitHub token and repo are required")
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = self.client.get(
                f"https://api.github.com/repos/{self.repo}/issues",
                headers=headers,
                params={"state": status},
                timeout=30.0
            )
            response.raise_for_status()
            
            issues = response.json()
            tickets = []
            
            for issue in issues:
                # Skip pull requests
                if "pull_request" in issue:
                    continue
                
                ticket = Ticket(
                    id=issue["number"],
                    title=issue["title"],
                    description=issue["body"] or "",
                    status=issue["state"],
                    labels=[label["name"] for label in issue.get("labels", [])],
                    assignee=issue.get("assignee", {}).get("login") if issue.get("assignee") else None
                )
                tickets.append(ticket)
            
            return tickets
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to list GitHub issues: {e}")
            raise
    
    def update_ticket(self, ticket_id: int, **kwargs) -> Ticket:
        """Update ticket"""
        if self.provider == "github":
            return self._github_update_ticket(ticket_id, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _github_update_ticket(self, ticket_id: int, **kwargs) -> Ticket:
        """Update GitHub issue"""
        if not self.token or not self.repo:
            raise ValueError("GitHub token and repo are required")
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        # Filter valid GitHub issue fields
        valid_fields = {"title", "body", "state", "labels"}
        data = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        try:
            response = self.client.patch(
                f"https://api.github.com/repos/{self.repo}/issues/{ticket_id}",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            return Ticket(
                id=result["number"],
                title=result["title"],
                description=result["body"] or "",
                status=result["state"],
                labels=[label["name"] for label in result.get("labels", [])],
                assignee=result.get("assignee", {}).get("login") if result.get("assignee") else None
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to update GitHub issue: {e}")
            raise
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
