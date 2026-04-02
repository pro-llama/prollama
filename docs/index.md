# prollama Documentation

**Intelligent LLM Execution Layer for developer teams.**

Anonymize code → route to the cheapest capable model → solve tickets autonomously.

## Contents

1. [Quickstart](quickstart.md) — install and solve your first task in 60 seconds
2. [Configuration](configuration.md) — YAML config, providers, privacy levels
3. [Anonymization](anonymization.md) — three-layer pipeline: regex → NLP → AST
4. [Model Routing](routing.md) — cost-optimized escalation strategy
5. [Task Executor](executor.md) — the solve loop: classify → select → execute → iterate
6. [Proxy Server](proxy.md) — OpenAI-compatible proxy with built-in anonymization
7. [Interactive Shell](shell.md) — REPL for task solving and management
8. [CLI Reference](cli-reference.md) — all commands and options
9. [API Reference](api-reference.md) — Python API for programmatic use
10. [pyqual Integration](pyqual-integration.md) — using prollama as a fix provider
11. [Deployment](deployment.md) — Docker, self-hosted, CI/CD

## Architecture Overview

```
                    ┌─────────────────────────────┐
                    │         User / IDE           │
                    │  (any OpenAI-compatible tool) │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │      prollama proxy          │
                    │   localhost:8741/v1           │
                    ├─────────────────────────────┤
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │   Anonymization Pipeline│  │
                    │  │  ┌──────┐ ┌───┐ ┌───┐ │  │
                    │  │  │Regex │→│NLP│→│AST│ │  │
                    │  │  └──────┘ └───┘ └───┘ │  │
                    │  └────────────────────────┘  │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │    Model Router         │  │
                    │  │  cheap → mid → premium  │  │
                    │  └────────────────────────┘  │
                    │                              │
                    └──┬───────┬────────┬─────────┘
                       │       │        │
              ┌────────▼┐ ┌───▼────┐ ┌─▼────────┐
              │  Ollama  │ │ OpenAI │ │Anthropic │
              │ (local)  │ │(cloud) │ │ (cloud)  │
              └──────────┘ └────────┘ └──────────┘
```

## Key Concepts

**Anonymization** — prollama strips sensitive data from code before it reaches any LLM.
Three layers work together: regex catches secrets and tokens, NLP catches person names
in comments, AST renames business-logic identifiers. After the LLM responds, prollama
reverses the mapping (rehydration) and returns code with original names.

**Model Routing** — instead of always using the most expensive model, prollama starts
with the cheapest one that might work. If it fails after N iterations, it escalates to
the next tier. This reduces costs by 60-80% for typical workloads.

**Task Execution** — prollama doesn't just proxy requests. It accepts a task description
(or a GitHub issue), classifies complexity, selects a strategy, generates a fix, runs
tests, and iterates until the fix passes or the budget is exhausted.

## Quick Links

- [GitHub Repository](https://github.com/softreck/prollama)
- [PyPI Package](https://pypi.org/project/prollama/)
- [pyqual Ecosystem](https://pyqual.dev)
- [Issue Tracker](https://github.com/softreck/prollama/issues)
