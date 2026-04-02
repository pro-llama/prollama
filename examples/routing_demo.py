#!/usr/bin/env python3
"""Example: Model routing and cost estimation.

Shows how prollama selects models based on task complexity
and estimates costs for different scenarios.
"""

from rich.console import Console
from rich.table import Table

from prollama.config import Config, ProviderConfig
from prollama.models import TaskComplexity
from prollama.router import ModelRouter

console = Console()


def demo_routing():
    """Demonstrate model selection and escalation."""

    # Configure with multiple providers
    config = Config(providers=[
        ProviderConfig(name="ollama", base_url="http://localhost:11434/v1"),
        ProviderConfig(name="openai", api_key="sk-test", models=["gpt-4o-mini", "gpt-4o"]),
        ProviderConfig(name="anthropic", api_key="sk-ant-test", models=["claude-sonnet-4-20250514"]),
    ])

    router = ModelRouter(config=config)

    # Show available models
    console.print("[bold]Available Models:[/]\n")
    table = Table(show_lines=False)
    table.add_column("Model", style="cyan")
    table.add_column("Provider")
    table.add_column("Tier")
    table.add_column("Cost (in/out per 1M)")
    table.add_column("Local")

    for m in sorted(router.available_models(), key=lambda x: x.cost_per_1m_input):
        cost = "free" if m.local else f"${m.cost_per_1m_input:.2f} / ${m.cost_per_1m_output:.2f}"
        table.add_row(m.name, m.provider, m.tier.value, cost, "✓" if m.local else "")

    console.print(table)

    # Show routing for each complexity level
    console.print("\n[bold]Routing by Task Complexity:[/]\n")
    for complexity in TaskComplexity:
        model = router.select(complexity=complexity)
        if model:
            cost_40_tasks = router.estimate_cost(model, 2000, 500) * 40
            console.print(
                f"  {complexity.value:12s} → [cyan]{model.name:30s}[/] "
                f"({model.tier.value:8s}) "
                f"~${cost_40_tasks:.2f}/month at 40 tasks"
            )

    # Show escalation chain
    console.print("\n[bold]Escalation Chain:[/]\n")
    model = router.select(complexity=TaskComplexity.SIMPLE)
    chain = []
    while model:
        chain.append(model)
        model = router.escalate(model)

    for i, m in enumerate(chain):
        arrow = "  →  " if i > 0 else "     "
        console.print(f"{arrow}[cyan]{m.name}[/] ({m.tier.value})")

    # Cost comparison
    console.print("\n[bold]Monthly Cost Comparison (40 tasks/month):[/]\n")
    scenarios = [
        ("All cheap (cost-optimized)", TaskComplexity.SIMPLE, 40),
        ("Mixed (realistic)", None, 40),
        ("All premium", TaskComplexity.HARD, 40),
    ]
    for name, complexity, count in scenarios:
        if complexity:
            model = router.select(complexity=complexity)
            cost = router.estimate_cost(model, 2000, 500) * count if model else 0
        else:
            # Simulate realistic mix: 45% simple, 30% medium, 18% hard, 7% very hard
            cost = 0
            for c, pct in [
                (TaskComplexity.SIMPLE, 0.45),
                (TaskComplexity.MEDIUM, 0.30),
                (TaskComplexity.HARD, 0.18),
                (TaskComplexity.VERY_HARD, 0.07),
            ]:
                m = router.select(complexity=c)
                if m:
                    cost += router.estimate_cost(m, 2000, 500) * count * pct
        console.print(f"  {name:35s} ${cost:.2f}")


if __name__ == "__main__":
    demo_routing()
