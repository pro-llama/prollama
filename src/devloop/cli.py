"""CLI — the devloop command.

Usage:
    devloop init ./my-app           # initialize
    devloop analyze                 # run all analysis
    devloop plan                    # generate sprint plan
    devloop go                      # full pipeline
    devloop status                  # dashboard

    devloop ask "question"          # quick LLM query
    devloop ticket add "title"      # add ticket
    devloop ticket list             # show tickets
    devloop sync                    # push to GitHub/Jira

    devloop algo discover           # start trace collection
    devloop algo extract            # find patterns
    devloop algo rules              # generate deterministic replacements
    devloop algo report             # show progress

    devloop workflow run f.md       # execute Propact workflow
    devloop workflow validate f.md  # check syntax
    devloop tools                   # show installed tools
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="devloop",
    help="Progressive algorithmization toolchain — from LLM to deterministic, from proxy to tickets.",
    no_args_is_help=True,
)
ticket_app = typer.Typer(help="Manage tickets.")
algo_app = typer.Typer(help="Progressive algorithmization.")
workflow_app = typer.Typer(help="Propact Markdown workflows.")
app.add_typer(ticket_app, name="ticket")
app.add_typer(algo_app, name="algo")
app.add_typer(workflow_app, name="workflow")

console = Console()


@app.command()
def init(path: str = typer.Argument(".", help="Project directory")):
    """Initialize devloop for a project."""
    from devloop.config import Config
    from devloop.tools import discover_tools

    project_path = Path(path).resolve()
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / ".devloop").mkdir(exist_ok=True)

    cfg = Config.load()
    cfg_path = cfg.save(str(project_path / "devloop.yaml"))

    console.print(f"\n[bold green]\u2705 devloop initialized[/] in {project_path}")
    console.print(f"   Config: {cfg_path}")

    tools = discover_tools()
    table = Table(title="Available Tools")
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Role")
    from devloop.tools import TOOL_REGISTRY
    for name, status in tools.items():
        table.add_row(name, str(status), TOOL_REGISTRY[name]["role"])
    console.print(table)

    missing = [n for n, s in tools.items() if not s.installed]
    if missing:
        console.print(f"\n[yellow]Install missing:[/] pip install {' '.join(missing)}")


@app.command()
def analyze(
    path: str = typer.Option(".", "--path", "-p"),
    quick: bool = typer.Option(False, "--quick", "-q"),
):
    """Analyze project health."""
    from devloop.project import Project
    with console.status("Analyzing..."):
        p = Project(path)
        report = p.analyze(full=not quick)
    console.print(f"\n[bold]Health Report[/]")
    console.print(report.summary())
    if report.grade in ("A", "B"):
        console.print(f"[bold green]Grade {report.grade}[/] — looking good!")
    else:
        console.print(f"[bold yellow]Grade {report.grade}[/] — run [bold]devloop plan[/] for improvements.")


@app.command()
def plan(
    path: str = typer.Option(".", "--path", "-p"),
    sprints: int = typer.Option(2, "--sprints", "-s"),
    focus: str = typer.Option("complexity", "--focus", "-f"),
):
    """Generate sprint plan with auto-tickets."""
    from devloop.project import Project
    with console.status("Planning..."):
        p = Project(path)
        result = p.plan(sprints=sprints, focus=focus)
    console.print(f"\n[bold]Sprint Plan[/]")
    console.print(result["summary"])
    console.print(f"\nTickets created: [bold]{result['tickets_created']}[/]")
    if result["tickets"]:
        table = Table(title="New Tickets")
        table.add_column("ID"); table.add_column("Priority")
        table.add_column("Type"); table.add_column("Title")
        for t in result["tickets"][:15]:
            table.add_row(t["id"], t["priority"], t["type"], t["title"])
        console.print(table)


@app.command()
def go(
    path: str = typer.Option(".", "--path", "-p"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """Full pipeline: analyze \u2192 plan \u2192 execute \u2192 validate."""
    from devloop.workflows import Pipeline
    console.print("[bold]Starting full pipeline...[/]\n")
    pipeline = Pipeline(path)
    with console.status("[1/4] Analyzing..."):
        pipeline.analyze()
    console.print("\u2705 Analysis complete")
    with console.status("[2/4] Creating tickets..."):
        pipeline.create_tickets()
    console.print("\u2705 Tickets created")
    if not dry_run:
        with console.status("[3/4] Executing..."):
            pipeline.execute()
        console.print("\u2705 Execution complete")
        with console.status("[4/4] Validating..."):
            pipeline.validate()
        console.print("\u2705 Validation complete")
    result = pipeline.report()
    for step in result["steps"]:
        console.print(f"  {step}")


@app.command()
def status(path: str = typer.Option(".", "--path", "-p")):
    """Show project status dashboard."""
    from devloop.project import Project
    with console.status("Checking status..."):
        p = Project(path)
        s = p.status()

    h = s["health"]
    console.print(f"\n[bold]Project:[/] {s['project']}")
    console.print(
        f"[bold]Health:[/] Grade {h['grade']} | CC\u0304={h['cc_avg']:.1f} | "
        f"vallm={h['vallm_pass_rate']:.0%} | {h['files']} files"
    )
    t = s["tickets"]
    console.print(
        f"[bold]Tickets:[/] {t['open']} open, {t['in_progress']} wip, "
        f"{t['done']} done, {t['blocked']} blocked"
    )
    a = s["algo"]
    console.print(
        f"[bold]Algo:[/] stage={a['stage']} | "
        f"{a['deterministic_ratio']} deterministic | "
        f"{a['rules_active']} rules active | "
        f"saved ${a['saved_cost_usd']:.2f}"
    )
    console.print(
        f"[bold]Cost:[/] ${s['cost_ledger']['total_spent_usd']:.2f} total"
    )


@app.command()
def tools():
    """Show available tools and their status."""
    from devloop.tools import discover_tools, TOOL_REGISTRY
    all_tools = discover_tools()
    table = Table(title="devloop Toolchain")
    table.add_column("Tool", style="bold")
    table.add_column("Installed"); table.add_column("Version")
    table.add_column("CLI"); table.add_column("Role")
    for name, status in all_tools.items():
        table.add_row(
            name,
            "\u2705" if status.installed else "\u274c",
            status.version or "-",
            "\u2705" if status.cli_available else "\u274c",
            TOOL_REGISTRY[name]["role"],
        )
    console.print(table)


@app.command()
def ask(
    prompt: str = typer.Argument(...),
    tier: Optional[str] = typer.Option(None, "--tier", "-t"),
):
    """Quick LLM query via proxym."""
    from devloop.tools.proxy import Proxy
    with console.status("Thinking..."):
        with Proxy() as proxy:
            resp = proxy.ask(prompt, tier=tier)
    console.print(resp.content)
    if resp.model:
        console.print(f"\n[dim]Model: {resp.model} | Cost: ${resp.cost_usd:.4f}[/]")


@app.command()
def sync():
    """Sync tickets to external backend."""
    from devloop.tools.tickets import Tickets
    t = Tickets()
    console.print(f"Sync: {t.sync()}")


# ── Ticket subcommands ───────────────────────────────────

@ticket_app.command("add")
def ticket_add(
    title: str = typer.Argument(...),
    priority: str = typer.Option("normal", "--priority", "-p"),
    type: str = typer.Option("task", "--type", "-t"),
):
    """Add a new ticket."""
    from devloop.tools.tickets import Tickets
    ticket = Tickets().add(title, priority=priority, type=type)
    console.print(f"\u2705 Created: [bold]{ticket.id}[/] \u2014 {ticket.title}")


@ticket_app.command("list")
def ticket_list(status: Optional[str] = typer.Option(None, "--status", "-s")):
    """List tickets."""
    from devloop.tools.tickets import Tickets
    tickets = Tickets().list(status=status)
    if not tickets:
        console.print("No tickets."); return
    table = Table(title="Tickets")
    table.add_column("ID"); table.add_column("Status")
    table.add_column("Priority"); table.add_column("Type"); table.add_column("Title")
    for t in tickets:
        table.add_row(t.id, t.status, t.priority, t.type, t.title)
    console.print(table)


@ticket_app.command("board")
def ticket_board():
    """Kanban board view."""
    from devloop.tools.tickets import Tickets
    for col, tickets in Tickets().board().items():
        if tickets:
            console.print(f"\n[bold]{col.upper()}[/] ({len(tickets)})")
            for t in tickets:
                console.print(f"  [{t.priority}] {t.id}: {t.title}")


# ── Algo subcommands ─────────────────────────────────────

@algo_app.command("discover")
def algo_discover(path: str = typer.Option(".", "--path", "-p")):
    """Stage 1: Start trace collection from proxym."""
    from devloop.algo import Loop
    loop = Loop(path)
    loop.discover()
    console.print("\u2705 Discovery mode active. Traces will be collected from proxym.")
    console.print("Use your IDE normally \u2014 devloop records every LLM interaction.")


@algo_app.command("extract")
def algo_extract(
    path: str = typer.Option(".", "--path", "-p"),
    min_freq: int = typer.Option(3, "--min-freq"),
):
    """Stage 2: Extract repeating patterns from traces."""
    from devloop.algo import Loop
    loop = Loop(path)
    patterns = loop.extract(min_frequency=min_freq)
    if not patterns:
        console.print("No patterns found yet. Collect more traces first.")
        return
    table = Table(title="Extracted Patterns")
    table.add_column("ID"); table.add_column("Frequency")
    table.add_column("Avg Cost"); table.add_column("Description")
    for p in patterns[:10]:
        table.add_row(p.id, str(p.frequency), f"${p.avg_cost_usd:.4f}", p.description[:60])
    console.print(table)


@algo_app.command("rules")
def algo_rules(
    path: str = typer.Option(".", "--path", "-p"),
    no_llm: bool = typer.Option(False, "--no-llm"),
):
    """Stage 3: Generate deterministic rules for top patterns."""
    from devloop.algo import Loop
    loop = Loop(path)
    with console.status("Generating rules..."):
        rules = loop.generate_rules(use_llm=not no_llm)
    console.print(f"\u2705 Generated {len(rules)} rules")
    for r in rules:
        console.print(f"  {r.pattern_id}: {r.name} ({r.type})")


@algo_app.command("report")
def algo_report(path: str = typer.Option(".", "--path", "-p")):
    """Show algorithmization progress."""
    from devloop.algo import Loop
    report = Loop(path).report()
    console.print(f"\n[bold]Progressive Algorithmization Report[/]")
    console.print(f"Stage: [bold]{report['stage']}[/]")
    console.print(f"Total requests: {report['total_requests']}")
    console.print(f"Deterministic: [green]{report['deterministic_ratio']}[/]")
    console.print(f"Rules active: {report['rules_active']}")
    console.print(f"Cost saved: [green]${report['saved_cost_usd']:.2f}[/]")


# ── Workflow subcommands ─────────────────────────────────

@workflow_app.command("run")
def workflow_run(
    path: str = typer.Argument(..., help="Path to .md workflow"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """Execute a Propact Markdown workflow."""
    from devloop.project import Project
    p = Project(".")
    with console.status(f"Running workflow {path}..."):
        result = p.run_workflow(path, dry_run=dry_run)
    if result["success"]:
        console.print(f"\u2705 Workflow complete: {result['steps_done']} steps, ${result['total_cost_usd']:.4f}")
    else:
        console.print(f"\u274c Workflow failed: {result.get('steps_failed', 0)} steps failed")
        for err in result.get("errors", []):
            console.print(f"  {err}")


@workflow_app.command("validate")
def workflow_validate(path: str = typer.Argument(...)):
    """Check a Propact workflow for errors."""
    from devloop.propact import Workflow
    wf = Workflow(path)
    errors = wf.validate()
    if errors:
        console.print(f"\u274c {len(errors)} errors:")
        for e in errors:
            console.print(f"  {e}")
    else:
        steps = wf.parse()
        console.print(f"\u2705 Valid workflow: {len(steps)} steps")


if __name__ == "__main__":
    app()
