"""Interactive prollama shell — REPL for task solving and management.

Provides tab-completion, syntax highlighting, command history,
and a persistent session for working with prollama interactively.
"""

from __future__ import annotations

import shlex
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prollama import __version__
from prollama.config import Config
from prollama.models import PrivacyLevel, Task, TaskResult, TaskStatus

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

SHELL_STYLE = Style.from_dict({
    "prompt": "ansicyan bold",
    "command": "ansigreen",
})

HISTORY_FILE = Path.home() / ".prollama" / "shell_history"


# ---------------------------------------------------------------------------
# Completions
# ---------------------------------------------------------------------------

COMMANDS = [
    "solve", "anonymize", "status", "providers", "models", "config",
    "history", "cost", "help", "exit", "quit", "clear",
]

SOLVE_FLAGS = ["--file", "--error", "--ticket", "--dry-run", "--complexity", "--budget"]

completer = WordCompleter(COMMANDS + SOLVE_FLAGS, ignore_case=True)


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

class ProllamaShell:
    """Interactive REPL for prollama."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.console = Console()
        self.task_history: list[TaskResult] = []
        self.total_cost: float = 0.0

        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.session: PromptSession[str] = PromptSession(
            history=FileHistory(str(HISTORY_FILE)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
            style=SHELL_STYLE,
        )

    # -- main loop ----------------------------------------------------------

    def run(self) -> None:
        """Start the interactive shell."""
        self._print_welcome()

        while True:
            try:
                text = self.session.prompt(
                    HTML("<prompt>prollama</prompt> <command>▸</command> "),
                ).strip()

                if not text:
                    continue

                self._dispatch(text)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Ctrl+C — type 'exit' to quit[/]")
            except EOFError:
                self._cmd_exit()
                break

    # -- dispatcher ---------------------------------------------------------

    def _dispatch(self, text: str) -> None:
        """Parse and route a command."""
        try:
            parts = shlex.split(text)
        except ValueError:
            parts = text.split()

        cmd = parts[0].lower()
        args = parts[1:]

        handlers = {
            "solve": self._cmd_solve,
            "anonymize": self._cmd_anonymize,
            "anon": self._cmd_anonymize,
            "status": self._cmd_status,
            "providers": self._cmd_providers,
            "models": self._cmd_models,
            "config": self._cmd_config,
            "history": self._cmd_history,
            "cost": self._cmd_cost,
            "help": self._cmd_help,
            "clear": self._cmd_clear,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }

        handler = handlers.get(cmd)
        if handler:
            handler(args)
        else:
            # Treat unrecognized input as an implicit 'solve' command
            self._cmd_solve(parts)

    # -- commands -----------------------------------------------------------

    def _cmd_solve(self, args: list[str]) -> None:
        """Solve a task. Usage: solve <description> [--file PATH] [--error MSG]"""
        if not args:
            self.console.print("[yellow]Usage:[/] solve <description> [--file PATH] [--error MSG]")
            return

        # Parse flags
        file_path = None
        error = None
        ticket = None
        dry_run = False
        description_parts = []

        i = 0
        while i < len(args):
            if args[i] == "--file" and i + 1 < len(args):
                file_path = args[i + 1]
                i += 2
            elif args[i] == "--error" and i + 1 < len(args):
                error = args[i + 1]
                i += 2
            elif args[i] == "--ticket" and i + 1 < len(args):
                ticket = args[i + 1]
                i += 2
            elif args[i] == "--dry-run":
                dry_run = True
                i += 1
            else:
                description_parts.append(args[i])
                i += 1

        description = " ".join(description_parts)
        if not description:
            self.console.print("[yellow]Please provide a task description.[/]")
            return

        from prollama.executor import TaskExecutor
        from prollama.executor.task_executor import classify_complexity, classify_type

        task = Task(description=description, file_path=file_path, error=error, ticket_ref=ticket)
        task.complexity = classify_complexity(task)
        task.task_type = classify_type(task)

        executor = TaskExecutor(self.config)
        model = executor.router.select(complexity=task.complexity)

        self.console.print(f"\n[bold]Task:[/] {task.description}")
        self.console.print(
            f"  Type: [cyan]{task.task_type.value}[/]  "
            f"Complexity: [cyan]{task.complexity.value}[/]  "
            f"Model: [cyan]{model.name if model else 'none'}[/]"
        )

        if dry_run:
            self.console.print("[yellow]  (dry run — no execution)[/]\n")
            return

        self.console.print("[bold green]  Solving...[/]")
        result = executor.solve(task)

        if result.status == TaskStatus.COMPLETED:
            self.console.print(
                f"[green]  ✓[/] Solved in {result.iterations} iter, "
                f"{result.duration_seconds:.1f}s, ${result.cost_usd:.4f}"
            )
            if result.patch:
                self.console.print(Panel(result.patch, title="Patch", border_style="green", padding=(0, 1)))
        else:
            self.console.print(f"[red]  ✗[/] Failed: {result.error_message}")

        self.task_history.append(result)
        self.total_cost += result.cost_usd
        self.console.print()

    def _cmd_anonymize(self, args: list[str]) -> None:
        """Anonymize a file. Usage: anonymize <file>"""
        if not args:
            self.console.print("[yellow]Usage:[/] anonymize <file_path>")
            return

        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found:[/] {file_path}")
            return

        from prollama.anonymizer import AnonymizationPipeline

        code = file_path.read_text()
        pipeline = AnonymizationPipeline(
            privacy_level=PrivacyLevel(self.config.privacy.level),
        )
        result = pipeline.run(code)

        if result.stats:
            self.console.print("[bold]Found:[/]")
            for cat, count in sorted(result.stats.items()):
                self.console.print(f"  {cat}: [cyan]{count}[/]")

        self.console.print(Panel(result.anonymized_code, title="Anonymized", border_style="blue", padding=(0, 1)))
        self.console.print()

    def _cmd_status(self, args: list[str]) -> None:
        """Show current session status."""
        self.console.print(f"\n[bold]prollama[/] v{__version__}")
        self.console.print(f"  Privacy: [cyan]{self.config.privacy.level}[/]")
        self.console.print(f"  Routing: [cyan]{self.config.routing.strategy}[/]")
        self.console.print(f"  Providers: [cyan]{', '.join(self.config.provider_names()) or 'none'}[/]")
        self.console.print(f"  Session tasks: [cyan]{len(self.task_history)}[/]")
        self.console.print(f"  Session cost: [cyan]${self.total_cost:.4f}[/]\n")

    def _cmd_providers(self, args: list[str]) -> None:
        """List configured providers."""
        if not self.config.providers:
            self.console.print("[yellow]No providers configured.[/] Run [bold]prollama init[/]")
            return

        table = Table(title="Providers", show_lines=False)
        table.add_column("Name", style="cyan")
        table.add_column("URL")
        table.add_column("Models")
        table.add_column("Key")

        for p in self.config.providers:
            key_status = "✓" if p.resolve_api_key() else "—"
            table.add_row(p.name, p.base_url or "(default)", ", ".join(p.models), key_status)

        self.console.print(table)
        self.console.print()

    def _cmd_models(self, args: list[str]) -> None:
        """List available models across all providers."""
        from prollama.router import ModelRouter

        router = ModelRouter(config=self.config)
        available = router.available_models()

        if not available:
            self.console.print("[yellow]No models available.[/] Check your provider config.")
            return

        table = Table(title="Available Models", show_lines=False)
        table.add_column("Model", style="cyan")
        table.add_column("Provider")
        table.add_column("Tier")
        table.add_column("Cost (in/out per 1M)")
        table.add_column("Local")

        for m in sorted(available, key=lambda x: x.cost_per_1m_input):
            cost_str = "free" if m.local else f"${m.cost_per_1m_input:.2f} / ${m.cost_per_1m_output:.2f}"
            table.add_row(m.name, m.provider, m.tier.value, cost_str, "✓" if m.local else "")

        self.console.print(table)
        self.console.print()

    def _cmd_config(self, args: list[str]) -> None:
        """Show current config as JSON."""
        import json
        self.console.print_json(json.dumps(self.config.model_dump(mode="json"), indent=2))

    def _cmd_history(self, args: list[str]) -> None:
        """Show task history for this session."""
        if not self.task_history:
            self.console.print("[dim]No tasks solved in this session.[/]")
            return

        table = Table(title="Task History", show_lines=False)
        table.add_column("#", style="dim")
        table.add_column("Status")
        table.add_column("Model")
        table.add_column("Iter")
        table.add_column("Time")
        table.add_column("Cost")

        for i, r in enumerate(self.task_history, 1):
            status_icon = "[green]✓[/]" if r.status == TaskStatus.COMPLETED else "[red]✗[/]"
            table.add_row(
                str(i),
                status_icon,
                r.model_used or "—",
                str(r.iterations),
                f"{r.duration_seconds:.1f}s",
                f"${r.cost_usd:.4f}",
            )

        self.console.print(table)
        self.console.print(f"\n  Total cost: [bold]${self.total_cost:.4f}[/]\n")

    def _cmd_cost(self, args: list[str]) -> None:
        """Show accumulated cost."""
        self.console.print(f"\n  Session tasks: [cyan]{len(self.task_history)}[/]")
        self.console.print(f"  Total cost: [bold cyan]${self.total_cost:.4f}[/]\n")

    def _cmd_help(self, args: list[str]) -> None:
        """Show help."""
        self.console.print(Panel(
            "[bold]Commands:[/]\n\n"
            "  [cyan]solve[/] <description> [--file F] [--error E]   Solve a coding task\n"
            "  [cyan]anonymize[/] <file>                             Anonymize a source file\n"
            "  [cyan]status[/]                                       Session & config status\n"
            "  [cyan]providers[/]                                    List LLM providers\n"
            "  [cyan]models[/]                                       List available models\n"
            "  [cyan]config[/]                                       Show full configuration\n"
            "  [cyan]history[/]                                      Task history this session\n"
            "  [cyan]cost[/]                                         Accumulated cost summary\n"
            "  [cyan]clear[/]                                        Clear screen\n"
            "  [cyan]help[/]                                         This help\n"
            "  [cyan]exit[/] / [cyan]quit[/]                                    Exit shell\n"
            "\n[dim]Tip: type any text without a command to use it as a 'solve' description.[/]",
            title="prollama shell",
            border_style="cyan",
        ))

    def _cmd_clear(self, args: list[str]) -> None:
        """Clear the terminal."""
        self.console.clear()

    def _cmd_exit(self, args: list[str] | None = None) -> None:
        """Exit the shell."""
        if self.task_history:
            self.console.print(
                f"\n[dim]Session: {len(self.task_history)} tasks, ${self.total_cost:.4f} total cost[/]"
            )
        self.console.print("[dim]Bye![/]\n")
        raise SystemExit(0)

    # -- internals ----------------------------------------------------------

    def _print_welcome(self) -> None:
        self.console.print(Panel(
            f"[bold cyan]prollama shell[/] v{__version__}\n"
            f"[dim]Privacy: {self.config.privacy.level} │ "
            f"Routing: {self.config.routing.strategy} │ "
            f"Providers: {', '.join(self.config.provider_names()) or 'none'}[/]\n\n"
            "Type [bold]help[/] for commands or just describe a task to solve it.",
            border_style="cyan",
        ))
