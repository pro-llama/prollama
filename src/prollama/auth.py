"""GitHub authentication using OAuth Device Flow.

One-click login without local server:
1. User runs `prollama login`
2. Opens browser with device code
3. Polls GitHub for authorization
4. Stores token securely in ~/.prollama/credentials

Docs: https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps#device-flow
"""

from __future__ import annotations

import json
import os
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import httpx
from rich.console import Console
from rich.panel import Panel

console = Console()

# GitHub OAuth Device Flow endpoints
GITHUB_DEVICE_AUTH_URL = "https://github.com/login/device/code"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"

# prollama OAuth App (GitHub requires client_id, no secret needed for device flow)
PROLLAMA_CLIENT_ID = "Ov23liX8wN5q9DgTJvO8"  # Public client_id only


def get_credentials_path() -> Path:
    """Get path to secure credentials file."""
    creds_dir = Path.home() / ".prollama"
    creds_dir.mkdir(parents=True, exist_ok=True)
    return creds_dir / "credentials.json"


def save_github_token(token: str, username: str | None = None) -> None:
    """Save GitHub token securely."""
    creds_path = get_credentials_path()
    creds = {"github_token": token}
    if username:
        creds["github_username"] = username
    creds_path.write_text(json.dumps(creds, indent=2), mode="w")
    # Restrict permissions (owner read/write only)
    os.chmod(creds_path, 0o600)


def load_github_token() -> str | None:
    """Load GitHub token from secure storage."""
    creds_path = get_credentials_path()
    if creds_path.exists():
        try:
            creds = json.loads(creds_path.read_text())
            return creds.get("github_token")
        except Exception:
            return None
    return None


def get_github_username(token: str) -> str | None:
    """Get GitHub username from API."""
    try:
        response = httpx.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json().get("login")
    except Exception:
        return None


def login_device_flow() -> str | None:
    """GitHub OAuth Device Flow - one click login.
    
    Returns the access token or None if failed.
    """
    console.print("[bold]prollama login[/bold] — GitHub authentication\n")
    
    # Step 1: Request device code
    try:
        response = httpx.post(
            GITHUB_DEVICE_AUTH_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": PROLLAMA_CLIENT_ID,
                "scope": "repo user write:discussion"
            },
            timeout=30.0
        )
        response.raise_for_status()
        device_data = response.json()
        
        device_code = device_data["device_code"]
        user_code = device_data["user_code"]
        verification_uri = device_data["verification_uri"]
        expires_in = device_data["expires_in"]
        interval = device_data["interval"]
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initiate login: {e}")
        return None
    
    # Step 2: Show user code and open browser
    console.print(Panel(
        f"[bold cyan]{user_code}[/bold cyan]\n\n"
        f"[dim]Enter this code on GitHub to authenticate[/dim]",
        title="Your Device Code",
        border_style="cyan"
    ))
    
    # Open browser automatically
    console.print(f"Opening {verification_uri} ...")
    try:
        webbrowser.open(verification_uri)
    except Exception:
        pass  # Browser might not be available
    
    console.print(f"\n[yellow]⏳[/yellow] Waiting for authorization... (expires in {expires_in}s)\n")
    
    # Step 3: Poll for access token
    start_time = time.time()
    while time.time() - start_time < expires_in:
        try:
            token_response = httpx.post(
                GITHUB_OAUTH_TOKEN_URL,
                headers={
                    "Accept": "application/json"
                },
                data={
                    "client_id": PROLLAMA_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                },
                timeout=30.0
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            
            if "access_token" in token_data:
                token = token_data["access_token"]
                # Get username
                username = get_github_username(token)
                # Save securely
                save_github_token(token, username)
                
                console.print(f"[green]✓[/green] Logged in as [bold]{username or 'GitHub user'}[/bold]")
                console.print(f"  Token saved to {get_credentials_path()}")
                return token
            
            if "error" in token_data:
                error = token_data["error"]
                if error == "authorization_pending":
                    # Still waiting, continue polling
                    pass
                elif error == "slow_down":
                    # Increase interval
                    interval = token_data.get("interval", interval + 5)
                elif error == "expired_token":
                    console.print("[red]✗[/red] Device code expired. Please try again.")
                    return None
                elif error == "access_denied":
                    console.print("[red]✗[/red] Authorization denied by user.")
                    return None
                else:
                    console.print(f"[red]✗[/red] Error: {error}")
                    return None
            
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Poll error: {e}")
        
        time.sleep(interval)
    
    console.print("[red]✗[/red] Login timed out.")
    return None


def logout() -> bool:
    """Remove stored GitHub credentials."""
    creds_path = get_credentials_path()
    if creds_path.exists():
        creds_path.unlink()
        console.print("[green]✓[/green] Logged out. GitHub credentials removed.")
        return True
    else:
        console.print("[yellow]⚠[/yellow] Not logged in.")
        return False


def is_logged_in() -> bool:
    """Check if user is authenticated with GitHub."""
    return load_github_token() is not None


def get_auth_headers() -> dict[str, str] | None:
    """Get authorization headers for GitHub API."""
    token = load_github_token()
    if token:
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    return None
