"""prollama CLI — command-line interface and interactive shell.

Usage:
    prollama init [--provider NAME]
    prollama start [--port PORT]
    prollama stop
    prollama status
    prollama solve DESCRIPTION [--file PATH] [--error MSG]
    prollama anonymize FILE
    prollama config show
    prollama shell
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prollama import __version__
from prollama.config import DEFAULT_CONFIG_FILE, Config

console = Console()


# ── helpers ────────────────────────────────────────────────────────────────

def _load_config(ctx: click.Context) -> Config:
    config_path = ctx.obj.get("config") if ctx.obj else None
    return Config.load(Path(config_path) if config_path else None)


def _print_banner() -> None:
    console.print(
        Panel(
            f"[bold cyan]prollama[/] v{__version__}\n"
            "[dim]Intelligent LLM Execution Layer[/]",
            border_style="cyan",
        )
    )


# ── root group ─────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--config", "-c", "config_path", default=None, help="Path to config.yaml")
@click.option("--version", "-V", is_flag=True, help="Show version")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, version: bool) -> None:
    """prollama — Intelligent LLM Execution Layer for developer teams."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config_path

    if ctx.invoked_subcommand is None:
        if version:
            console.print(f"prollama {__version__}")
            ctx.exit(0)
        console.print(ctx.get_help())
        ctx.exit(1)


# ── login ──────────────────────────────────────────────────────────────────

@main.command()
def login() -> None:
    """Authenticate with GitHub using OAuth device flow."""
    from prollama.auth import login_device_flow
    login_device_flow()


# ── logout ─────────────────────────────────────────────────────────────────

@main.command()
def logout() -> None:
    """Remove stored GitHub credentials."""
    from prollama.auth import logout
    logout()


# ── init ───────────────────────────────────────────────────────────────────

@main.command()
@click.option("--provider", "-p", default="ollama", help="Default provider (ollama, openai, anthropic)")
@click.pass_context
def init(ctx: click.Context, provider: str) -> None:
    """Initialize prollama configuration."""
    config_path = Path(ctx.obj.get("config") or DEFAULT_CONFIG_FILE)
    if config_path.exists():
        if not click.confirm(f"Config already exists at {config_path}. Overwrite?"):
            return

    path = Config.write_template(config_path)
    console.print(f"[green]✓[/] Config created at [bold]{path}[/]")
    console.print(f"  Default provider: [cyan]{provider}[/]")
    console.print("\n  Edit the file to add your API keys, then run [bold]prollama start[/]")


# ── start ──────────────────────────────────────────────────────────────────

@main.command()
@click.option("--host", default=None, help="Proxy bind host")
@click.option("--port", "-p", default=None, type=int, help="Proxy port")
@click.pass_context
def start(ctx: click.Context, host: str | None, port: int | None) -> None:
    """Start the prollama proxy server."""
    config = _load_config(ctx)

    bind_host = host or config.proxy.host
    bind_port = port or config.proxy.port

    console.print(f"[green]▶[/] Starting prollama proxy on [bold]{bind_host}:{bind_port}[/]")
    console.print(f"  Privacy level: [cyan]{config.privacy.level}[/]")
    console.print(f"  Routing: [cyan]{config.routing.strategy}[/]")
    console.print(f"  Providers: [cyan]{', '.join(config.provider_names()) or 'none configured'}[/]")
    console.print(f"\n  Set [bold]OPENAI_BASE_URL=http://{bind_host}:{bind_port}/v1[/] in your IDE")

    try:
        import uvicorn

        from prollama.proxy import create_app
        app = create_app(config)
        uvicorn.run(app, host=bind_host, port=bind_port, log_level="info")
    except ImportError:
        console.print(
            "\n[yellow]⚠[/] Proxy server requires FastAPI + uvicorn.\n"
            "  Install with: [bold]pip install prollama[proxy][/]"
        )
        sys.exit(1)


# ── stop ───────────────────────────────────────────────────────────────────

@main.command()
def stop() -> None:
    """Stop the prollama proxy server."""
    # In production this would signal a running daemon; for now, placeholder.
    console.print("[yellow]⏹[/] Proxy stop requested (use Ctrl+C on the running server)")


# ── status ─────────────────────────────────────────────────────────────────

@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show prollama status and configuration."""
    config = _load_config(ctx)

    _print_banner()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("Config", str(DEFAULT_CONFIG_FILE))
    table.add_row("Privacy", config.privacy.level)
    table.add_row("Routing", config.routing.strategy)
    table.add_row("Proxy", f"{config.proxy.host}:{config.proxy.port}")
    table.add_row("Max iterations", str(config.executor.max_iterations))
    table.add_row("Budget", f"${config.executor.budget:.2f}")

    console.print(table)

    if config.providers:
        console.print("\n[bold]Providers:[/]")
        for p in config.providers:
            models = ", ".join(p.models) if p.models else "auto"
            url = p.base_url or "(default)"
            key_status = "[green]✓ key set[/]" if p.resolve_api_key() else "[dim]no key[/]"
            console.print(f"  [cyan]{p.name}[/]  {url}  models=[dim]{models}[/]  {key_status}")
    else:
        console.print("\n[yellow]No providers configured.[/] Run [bold]prollama init[/]")


# ── solve ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("description")
@click.option("--file", "-f", "file_path", default=None, help="Source file to fix")
@click.option("--error", "-e", default=None, help="Error message or traceback")
@click.option("--ticket", "-t", default=None, help="Ticket ref (e.g. github:org/repo#142)")
@click.option("--dry-run", is_flag=True, help="Show what would happen without executing")
@click.option("--pr", is_flag=True, help="Create Pull Request with the fix")
@click.option("--draft-pr", is_flag=True, help="Create PR as draft")
@click.pass_context
def solve(
    ctx: click.Context,
    description: str,
    file_path: str | None,
    error: str | None,
    ticket: str | None,
    dry_run: bool,
    pr: bool,
    draft_pr: bool,
) -> None:
    """Solve a coding task using LLM orchestration."""
    from prollama.executor import TaskExecutor
    from prollama.models import Task

    config = _load_config(ctx)
    task = Task(
        description=description,
        file_path=file_path,
        error=error,
        ticket_ref=ticket,
    )

    executor = TaskExecutor(config)

    # Classify for display
    from prollama.executor.task_executor import classify_complexity, classify_type
    task.complexity = classify_complexity(task)
    task.task_type = classify_type(task)

    console.print(f"\n[bold]Task:[/] {task.description}")
    console.print(f"  ID: [dim]{task.id}[/]")
    console.print(f"  Type: [cyan]{task.task_type.value}[/]  Complexity: [cyan]{task.complexity.value}[/]")

    if file_path:
        console.print(f"  File: [dim]{file_path}[/]")

    model = executor.router.select(complexity=task.complexity)
    if model:
        console.print(f"  Model: [cyan]{model.name}[/] ({model.tier.value})")

    if dry_run:
        console.print("\n[yellow]Dry run — no changes made.[/]")
        return

    console.print("\n[bold green]Solving...[/]\n")
    result = executor.solve(task)

    if result.status.value == "completed":
        console.print(f"[green]✓[/] Solved in {result.iterations} iteration(s), {result.duration_seconds:.1f}s")
        console.print(f"  Model: [cyan]{result.model_used}[/]  Cost: [dim]${result.cost_usd:.4f}[/]")
        if result.patch:
            console.print(Panel(result.patch, title="Patch", border_style="green"))
        
        # Create PR if requested
        if pr or draft_pr:
            from prollama.pr import create_pr_from_solve
            pr_data = create_pr_from_solve(
                task_description=description,
                patch=result.patch,
                cost_usd=result.cost_usd,
                model_used=result.model_used,
                iterations=result.iterations,
                file_path=file_path,
                draft=draft_pr
            )
            if pr_data:
                console.print(f"\n[green]✓[/green] Pull Request created!")
                console.print(f"  [cyan]#{pr_data['number']}[/cyan] {pr_data['title']}")
                console.print(f"  {pr_data['html_url']}")
    else:
        console.print(f"[red]✗[/] Failed: {result.error_message}")
        console.print(f"  Iterations: {result.iterations}  Cost: ${result.cost_usd:.4f}")


# ── anonymize ──────────────────────────────────────────────────────────────

@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--level", "-l", default=None, type=click.Choice(["none", "basic", "full"]))
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
@click.pass_context
def anonymize(ctx: click.Context, file_path: str, level: str | None, output: str | None) -> None:
    """Anonymize a source file and show results."""
    from prollama.anonymizer import AnonymizationPipeline
    from prollama.models import PrivacyLevel

    config = _load_config(ctx)
    privacy_level = PrivacyLevel(level) if level else PrivacyLevel(config.privacy.level)

    code = Path(file_path).read_text()
    pipeline = AnonymizationPipeline(privacy_level=privacy_level)
    result = pipeline.run(code)

    if result.stats:
        console.print("[bold]Anonymization report:[/]")
        for category, count in sorted(result.stats.items()):
            console.print(f"  {category}: [cyan]{count}[/] item(s) found & replaced")
        console.print()

    if output:
        Path(output).write_text(result.anonymized_code)
        console.print(f"[green]✓[/] Written to {output}")
    else:
        console.print(Panel(result.anonymized_code, title="Anonymized", border_style="blue"))

    if result.mappings:
        console.print("\n[bold]Mappings (for rehydration):[/]")
        for m in result.mappings[:20]:
            console.print(f"  {m.replacement} ← [dim]{m.original[:40]}{'…' if len(m.original) > 40 else ''}[/]")
        if len(result.mappings) > 20:
            console.print(f"  [dim]... and {len(result.mappings) - 20} more[/]")


# ── config ─────────────────────────────────────────────────────────────────

@main.group(name="config")
def config_group() -> None:
    """Manage prollama configuration."""
    pass


@config_group.command(name="show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration."""
    config = _load_config(ctx)
    console.print_json(json.dumps(config.model_dump(mode="json"), indent=2))


@config_group.command(name="path")
def config_path() -> None:
    """Show config file path."""
    console.print(str(DEFAULT_CONFIG_FILE))


# ── shell ──────────────────────────────────────────────────────────────────

@main.command()
@click.pass_context
def shell(ctx: click.Context) -> None:
    """Start interactive prollama shell."""
    from prollama.shell import ProllamaShell
    config = _load_config(ctx)
    ProllamaShell(config).run()


# ── entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
