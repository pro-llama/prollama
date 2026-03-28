# devloop

**Progressive algorithmization toolchain — from LLM to deterministic code, from proxy to tickets.**

> The only framework that automates the path from "LLM handles everything"
> to "most traffic runs deterministically, LLM only for edge cases."

```
pip install devloop
devloop init ./my-app
devloop go
```

## Why "devloop"?

The name reflects the core cycle: **analyze → plan → execute → validate → repeat**. Each iteration makes your codebase healthier and your LLM usage cheaper. The progressive algorithmization loop gradually replaces LLM calls with deterministic rules.

## Name alternatives considered

| Name | Why it works | Why we picked devloop |
|------|-------------|----------------------|
| **devloop** | Core concept: the continuous improvement loop | Clear, memorable, tech-neutral |
| prollama | "progressive" + llama vibes | Ties too much to one model family |
| codefact | Code + factory/fact | Sounds like a trivia app |
| algopact | Algorithm + Propact | Hard to pronounce |
| loopcode | Loop + code | Reverse reads awkward |
| prodev | Progressive + dev | Too generic, SEO nightmare |

## Three layers, one command

### Layer 1: Code Quality Loop
```python
from devloop import Project

p = Project("./my-app")
p.analyze()    # code2llm + vallm + redup → health report
p.plan()       # auto-generate tickets from analysis
p.execute()    # LLM handles tasks via proxym
p.status()     # health + tickets + budget + cost ledger
```

### Layer 2: Progressive Algorithmization
```python
from devloop import Loop

loop = Loop("./my-app")
loop.discover()        # Stage 1: collect all LLM traces
loop.extract()         # Stage 2: find repeating patterns
loop.generate_rules()  # Stage 3: AI writes its own replacement
loop.route()           # Stage 4: rules vs LLM by confidence
loop.optimize()        # Stage 5: monitor, minimize LLM usage
print(loop.report())   # "42% deterministic, $12.50 saved"
```

### Layer 3: Propact Workflows
```python
from devloop import Workflow

wf = Workflow("./refactor-v1.md")
wf.execute()   # runs propact:shell, propact:rest, propact:llm blocks
```

## CLI

```bash
# Core loop
devloop init ./my-app         # initialize project
devloop analyze               # health check
devloop plan --sprints 3      # generate sprint strategy + tickets
devloop go                    # full pipeline
devloop status                # dashboard

# Progressive algorithmization
devloop algo discover         # start trace collection
devloop algo extract          # find patterns in traces
devloop algo rules            # generate deterministic replacements
devloop algo report           # show % deterministic vs LLM

# Propact workflows
devloop workflow run fix.md   # execute Markdown workflow
devloop workflow validate f.md

# Tickets
devloop ticket add "Fix auth" --priority high
devloop ticket list
devloop ticket board
devloop sync                  # push to GitHub/Jira

# Quick queries
devloop ask "Explain this race condition" --tier premium
devloop tools                 # show installed tools
```

## The 5-Stage Progressive Algorithmization

```
Stage 1: Discovery     → LLM handles 100%, collect traces
Stage 2: Extraction    → identify hot paths + repeating patterns
Stage 3: Rules         → AI generates deterministic replacements
Stage 4: Hybrid        → confidence-based: known patterns → rules, unknown → LLM
Stage 5: Optimization  → most traffic deterministic, LLM for edge cases only
```

No existing framework automates this path. DSPy goes LLM→smaller LLM. devloop goes LLM→algorithm.

## Propact: Markdown as Workflow

```markdown
# Fix Authentication Module

Analyze current state:

```propact:shell
code2llm ./src/auth -f toon --json
```

Ask LLM for a fix plan:

```propact:rest
POST http://localhost:4000/v1/chat/completions
{"model": "balanced", "messages": [{"role": "user", "content": "Fix auth"}]}
```

Validate the result:

```propact:shell
vallm batch ./src/auth --recursive
```
```

## Planfile-Aware Proxy Headers

Every LLM request through devloop carries context:

```
X-Planfile-Ref: my-project/current/DLP-0042
X-Workflow-Ref: refactor-v1.md
X-Task-Tier: complex
X-Inject-Context: true
```

Proxym logs cost/model/latency **per ticket**. The cost ledger shows exactly what each task costs.

## Installation

```bash
pip install devloop                # core
pip install devloop[all]           # + all tools
pip install devloop[proxy]         # + proxym
pip install devloop[analysis]      # + code2llm, vallm, redup
pip install devloop[tickets]       # + planfile
pip install devloop[routing]       # + llx
```

## Architecture

```
src/devloop/
├── __init__.py           # Project, Loop, Workflow, Config, Pipeline
├── config.py             # Unified config (env + YAML)
├── project.py            # Main Project class (expanded)
├── cli.py                # Typer CLI (all commands)
├── algo/                 # Progressive algorithmization
│   ├── __init__.py       # Loop, TraceEntry, Pattern, Rule, LoopState
│   └── loop.py           # Re-export
├── propact/              # Markdown workflow engine
│   ├── __init__.py       # Workflow, WorkflowStep, WorkflowResult
│   └── workflow.py       # Re-export
├── tools/
│   ├── __init__.py       # Tool discovery
│   ├── proxy.py          # proxym wrapper + planfile headers
│   ├── analysis.py       # code2llm + vallm + redup
│   └── tickets.py        # planfile wrapper + cost ledger
└── workflows/
    ├── __init__.py        # Pipeline (composable steps)
    └── pipeline.py        # Re-export
```

## How it connects to the ecosystem

```
┌─────────────────────────────────────────────────────┐
│                     devloop                         │
│            (orchestration layer)                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  analyze()   plan()   execute()   algo.discover()   │
│     │          │         │            │             │
│  code2llm   planfile   proxym      trace →          │
│  vallm      tickets    llx         patterns →       │
│  redup      strategy   models      rules →          │
│                                    hybrid routing    │
│                                                     │
│  run_workflow("fix.md")                             │
│     │                                               │
│  propact:shell → subprocess                         │
│  propact:rest  → httpx                              │
│  propact:llm   → proxym                             │
│  propact:mcp   → MCP tool call                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Tool Roles

| Tool | What | Install |
|------|------|---------|
| **proxym** | LLM gateway, 10 providers, routing, budget | `pip install proxym` |
| **planfile** | Sprint planning, tickets, GitHub/Jira sync | `pip install planfile` |
| **llx** | Metric-driven model selection, MCP server | `pip install llx` |
| **code2llm** | Static analysis → .toon diagnostics | `pip install code2llm` |
| **vallm** | 4-tier code validation | `pip install vallm` |
| **redup** | Duplication detection | `pip install redup` |

## License

Licensed under Apache-2.0.


Apache License 2.0

## Author

Tom Sapletta


Created by **Tom Sapletta** — [tom@sapletta.com](mailto:tom@sapletta.com)

Part of the [semcod](https://github.com/semcod) / [wronai](https://github.com/wronai) ecosystem.
