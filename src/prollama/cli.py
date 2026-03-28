"""
Command Line Interface for Prollama
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .core import ProllamaCore
from .llm import LLMInterface, Message
from .proxy import ProxyManager, ProxyConfig, ProxyRequest
from .tickets import TicketManager, TicketCreate

console = Console()
app = typer.Typer(help="Prollama - Progressive algorithmization toolchain")


@app.command()
def version():
    """Show version information"""
    console.print(Panel(f"[bold blue]Prollama v0.1.1[/bold blue]\nFrom LLM to deterministic code, from proxy to tickets"))


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="Configuration key to get/set"),
    value: Optional[str] = typer.Argument(None, help="Configuration value to set"),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Manage configuration"""
    core = ProllamaCore(config_path)
    
    if key is None:
        # Show all configuration
        console.print("[bold]Current configuration:[/bold]")
        console.print(core.config)
    elif value is None:
        # Get specific configuration value
        config_value = core.get_config_value(key)
        console.print(f"[bold]{key}[/bold]: {config_value}")
    else:
        # Set configuration value
        core.set_config_value(key, value)
        core.save_config()
        console.print(f"[green]✓[/green] Set {key} = {value}")


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="Prompt to send to LLM"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to use"),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Chat with LLM"""
    core = ProllamaCore(config_path)
    
    # Get LLM configuration
    api_key = core.get_config_value("llm.api_key")
    provider = core.get_config_value("llm.provider", "openai")
    model_name = model or core.get_config_value("llm.model", "gpt-3.5-turbo")
    
    if not api_key:
        console.print("[red]✗[/red] LLM API key not configured. Set it with: prollama config llm.api_key YOUR_KEY")
        raise typer.Exit(1)
    
    # Initialize LLM interface
    llm = LLMInterface(provider=provider, api_key=api_key, model=model_name)
    
    try:
        console.print(f"[blue]🤖[/blue] Sending prompt to {model_name}...")
        response = llm.simple_chat(prompt, system)
        
        console.print("[bold]Response:[/bold]")
        console.print(Panel(response))
        
    except Exception as e:
        console.print(f"[red]✗[/red] Chat failed: {e}")
        raise typer.Exit(1)
    finally:
        llm.close()


@app.command()
def proxy_test(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Test proxy connectivity"""
    core = ProllamaCore(config_path)
    
    # Get proxy configuration
    proxy_config = ProxyConfig(
        host=core.get_config_value("proxy.host", "localhost"),
        port=core.get_config_value("proxy.port", 8080),
        enabled=core.get_config_value("proxy.enabled", False)
    )
    
    proxy_manager = ProxyManager(proxy_config)
    
    try:
        console.print("[blue]🔗[/blue] Testing proxy connectivity...")
        success = proxy_manager.test_proxy()
        
        if success:
            console.print("[green]✓[/green] Proxy test passed")
        else:
            console.print("[red]✗[/red] Proxy test failed")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]✗[/red] Proxy test failed: {e}")
        raise typer.Exit(1)
    finally:
        proxy_manager.close()


@app.command()
def ticket_list(
    status: str = typer.Option("open", "--status", "-s", help="Ticket status (open/closed)"),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """List tickets"""
    core = ProllamaCore(config_path)
    
    # Get ticket configuration
    token = core.get_config_value("tickets.token")
    repo = core.get_config_value("tickets.repo")
    provider = core.get_config_value("tickets.provider", "github")
    
    if not token or not repo:
        console.print("[red]✗[/red] Ticket configuration incomplete. Set tickets.token and tickets.repo")
        raise typer.Exit(1)
    
    # Initialize ticket manager
    ticket_manager = TicketManager(provider=provider, token=token, repo=repo)
    
    try:
        console.print(f"[blue]📋[/blue] Listing {status} tickets...")
        tickets = ticket_manager.list_tickets(status)
        
        if not tickets:
            console.print(f"[yellow]⚠[/yellow] No {status} tickets found")
            return
        
        # Create table
        table = Table(title=f"{status.capitalize()} Tickets")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Labels", style="yellow")
        
        for ticket in tickets:
            table.add_row(
                str(ticket.id),
                ticket.title[:50] + "..." if len(ticket.title) > 50 else ticket.title,
                ticket.status,
                ", ".join(ticket.labels[:3])  # Show first 3 labels
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list tickets: {e}")
        raise typer.Exit(1)
    finally:
        ticket_manager.close()


@app.command()
def ticket_create(
    title: str = typer.Argument(..., help="Ticket title"),
    description: str = typer.Option(..., "--description", "-d", help="Ticket description"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Ticket priority"),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Create a new ticket"""
    core = ProllamaCore(config_path)
    
    # Get ticket configuration
    token = core.get_config_value("tickets.token")
    repo = core.get_config_value("tickets.repo")
    provider = core.get_config_value("tickets.provider", "github")
    
    if not token or not repo:
        console.print("[red]✗[/red] Ticket configuration incomplete. Set tickets.token and tickets.repo")
        raise typer.Exit(1)
    
    # Parse labels
    label_list = labels.split(",") if labels else []
    
    # Create ticket
    ticket_data = TicketCreate(
        title=title,
        description=description,
        labels=label_list,
        priority=priority
    )
    
    # Initialize ticket manager
    ticket_manager = TicketManager(provider=provider, token=token, repo=repo)
    
    try:
        console.print(f"[blue]📝[/blue] Creating ticket: {title}")
        ticket = ticket_manager.create_ticket(ticket_data)
        
        console.print(f"[green]✓[/green] Ticket created successfully!")
        console.print(f"ID: {ticket.id}")
        console.print(f"Title: {ticket.title}")
        console.print(f"Status: {ticket.status}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create ticket: {e}")
        raise typer.Exit(1)
    finally:
        ticket_manager.close()


if __name__ == "__main__":
    app()
