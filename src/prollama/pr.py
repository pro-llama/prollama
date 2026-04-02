"""GitHub PR creation for prollama.

Creates pull requests with AI-generated fixes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import httpx
from rich.console import Console

from prollama.auth import get_auth_headers, load_github_token, get_local_username

console = Console()


def get_current_repo() -> tuple[str, str] | None:
    """Get current GitHub owner/repo from git remote.
    
    Returns (owner, repo) or None if not a GitHub repo.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        
        url = result.stdout.strip()
        
        # Parse GitHub URLs
        if "github.com" in url:
            # Handle HTTPS: https://github.com/owner/repo.git
            if url.startswith("https://github.com/"):
                parts = url.replace("https://github.com/", "").replace(".git", "").split("/")
                if len(parts) >= 2:
                    return (parts[0], parts[1])
            # Handle SSH: git@github.com:owner/repo.git
            elif url.startswith("git@github.com:"):
                parts = url.replace("git@github.com:", "").replace(".git", "").split("/")
                if len(parts) >= 2:
                    return (parts[0], parts[1])
        
        return None
    except Exception:
        return None


def get_current_branch() -> str | None:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def create_branch(branch_name: str, base_branch: str = "main") -> bool:
    """Create and checkout new git branch."""
    try:
        # First checkout base branch and pull
        subprocess.run(
            ["git", "checkout", base_branch],
            capture_output=True,
            timeout=30
        )
        subprocess.run(
            ["git", "pull", "origin", base_branch],
            capture_output=True,
            timeout=30
        )
        
        # Create new branch
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create branch: {e}")
        return False


def commit_changes(message: str, files: list[str] | None = None) -> bool:
    """Stage and commit changes."""
    try:
        # Stage specific files or all
        if files:
            subprocess.run(
                ["git", "add"] + files,
                capture_output=True,
                timeout=30
            )
        else:
            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                timeout=30
            )
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to commit: {e}")
        return False


def push_branch(branch_name: str) -> bool:
    """Push branch to origin."""
    try:
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to push: {e}")
        return False


def create_pull_request(
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
    owner: str | None = None,
    repo: str | None = None,
    draft: bool = False
) -> dict | None:
    """Create GitHub Pull Request.
    
    Returns PR data dict with 'number', 'html_url', etc. or None on failure.
    """
    token = load_github_token()
    if not token:
        console.print("[red]✗[/red] Not logged in. Run: [bold]prollama login[/bold]")
        return None
    
    # Auto-detect repo if not provided
    if not owner or not repo:
        detected = get_current_repo()
        if detected:
            owner, repo = detected
        else:
            console.print("[red]✗[/red] Could not detect GitHub repo. Are you in a git repository?")
            return None
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
        "draft": draft
    }
    
    try:
        response = httpx.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers,
            json=data,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            # PR might already exist or invalid
            error_data = e.response.json()
            messages = error_data.get("errors", [])
            for msg in messages:
                if isinstance(msg, dict) and "message" in msg:
                    console.print(f"[red]✗[/red] GitHub: {msg['message']}")
                else:
                    console.print(f"[red]✗[/red] GitHub: {msg}")
        else:
            console.print(f"[red]✗[/red] Failed to create PR: {e}")
        return None
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create PR: {e}")
        return None


def create_pr_from_solve(
    task_description: str,
    patch: str | None,
    cost_usd: float,
    model_used: str,
    iterations: int,
    file_path: str | None = None,
    draft: bool = False
) -> dict | None:
    """Full workflow: create branch, commit, push, and open PR.
    
    Returns PR data or None on failure.
    """
    if not patch:
        console.print("[yellow]⚠[/yellow] No patch generated. Nothing to commit.")
        return None
    
    # Check if we're in a git repo
    repo_info = get_current_repo()
    if not repo_info:
        console.print("[yellow]⚠[/yellow] Not in a GitHub repository. PR creation skipped.")
        return None
    
    owner, repo = repo_info
    
    # Generate branch name from task
    import re
    branch_suffix = re.sub(r'[^a-zA-Z0-9]+', '-', task_description.lower())[:40].strip('-')
    branch_name = f"prollama/{branch_suffix}"
    
    # Create branch
    console.print(f"\n[yellow]⏳[/yellow] Creating branch [bold]{branch_name}[/bold]...")
    if not create_branch(branch_name):
        return None
    
    # Write patch to file if file_path provided
    files_to_commit = []
    if file_path:
        try:
            Path(file_path).write_text(patch)
            files_to_commit.append(file_path)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to write patch: {e}")
            return None
    else:
        # No file specified - skip PR creation
        console.print("[yellow]⚠[/yellow] No file path specified. Apply patch manually.")
        return None
    
    # Auto-detect user from git config
    local_user = get_local_username() or "unknown"
    
    # Commit with auto-detected user
    commit_msg = f"fix: {task_description}\n\nGenerated by prollama using {model_used}\nCost: ${cost_usd:.4f} | Iterations: {iterations}\nAuthor: {local_user}"
    console.print(f"[yellow]⏳[/yellow] Committing changes...")
    if not commit_changes(commit_msg, files_to_commit):
        return None
    
    # Push
    console.print(f"[yellow]⏳[/yellow] Pushing to origin...")
    if not push_branch(branch_name):
        return None
    
    # Create PR with auto-detected user
    pr_title = f"fix: {task_description}"
    pr_body = f"""## 🤖 AI-Generated Fix

**Task:** {task_description}
**Model:** {model_used}
**Cost:** ${cost_usd:.4f}
**Iterations:** {iterations}
**Author:** {local_user}

### Changes
```diff
{patch[:2000]}{'...' if len(patch) > 2000 else ''}
```

---
*Generated by [prollama](https://github.com/pro-llama/prollama)*
"""
    
    console.print(f"[yellow]⏳[/yellow] Creating Pull Request...")
    pr = create_pull_request(
        title=pr_title,
        body=pr_body,
        head_branch=branch_name,
        owner=owner,
        repo=repo,
        draft=draft
    )
    
    return pr
