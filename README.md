# prollama

**Intelligent LLM Execution Layer for developer teams.**

Anonymize code → route to the cheapest capable model → solve tickets autonomously.

[![CI](https://github.com/softreck/prollama/actions/workflows/ci.yml/badge.svg)](https://github.com/softreck/prollama/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)


## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.05-green) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fqwen%2Fqwen3-coder-next-lightgrey)

This project uses AI-generated code. Total cost: **$1.0500** with **7** AI commits.

Generated on 2026-04-02 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/models/openrouter/qwen/qwen3-coder-next)

---

## Why prollama?

AI coding tools send your code — secrets, business logic, customer names — to cloud LLMs. prollama sits between your tools and the LLM, stripping sensitive data before it leaves your machine.

**Three layers of anonymization:**

1. **Regex** — API keys, tokens, connection strings, emails, IPs (70+ patterns, <1ms)
2. **NLP** — Person names in comments, addresses, SSNs (heuristic or Presidio, ~5ms)
3. **AST** — Class/function/variable names via tree-sitter (business logic hidden, ~20ms)

```python
# BEFORE (what you write)                    # AFTER (what the LLM sees)
class StripePaymentProcessor:                class Class_001:
    def charge_customer(self, amount):           def var_001(self, var_002):
        key = "sk_live_4eC39HqL..."                  key = "[SECRET_001]"
        return self.stripe.charge(amount)            return self.var_003.var_004(var_002)
```

After the LLM responds, prollama reverses the mapping and returns code with your original names.

## Quick Start

```bash
pip install prollama

prollama init                    # Create config
prollama solve "Fix the TypeError in auth.py" --file src/auth.py --dry-run
prollama anonymize src/payment.py --level full
prollama shell                   # Interactive REPL
```

## Installation

```bash
pip install prollama              # Core CLI + shell
pip install prollama[ast]         # + tree-sitter AST anonymization (recommended)
pip install prollama[proxy]       # + FastAPI proxy server
pip install prollama[nlp]         # + Presidio ML-based PII detection
pip install prollama[all]         # Everything
pip install prollama[dev]         # + pytest, ruff, mypy
```

## Features

### CLI

| Command | Description |
|---------|-------------|
| `prollama init` | Create config at `~/.prollama/config.yaml` |
| `prollama start` | Start OpenAI-compatible proxy with anonymization |
| `prollama status` | Show config and provider status |
| `prollama solve DESC` | Solve a coding task via LLM orchestration |
| `prollama anonymize FILE` | Anonymize source code and show report |
| `prollama config show` | Show full config as JSON |
| `prollama shell` | Interactive REPL with tab-completion |

### Interactive Shell

```
$ prollama shell

╭─ prollama shell v0.1.0 ──────────────────────────────────╮
│ Privacy: full │ Routing: cost-optimized │ Providers: ollama│
│ Type help for commands or describe a task to solve it.    │
╰──────────────────────────────────────────────────────────╯

prollama ▸ Fix missing type hints in utils.py
  Task: Fix missing type hints in utils.py
  Type: fix  Complexity: simple  Model: qwen2.5-coder:7b
  Solving...
  ✓ Solved in 1 iter, 2.3s, $0.0000

prollama ▸ history
prollama ▸ models
prollama ▸ cost
```

### Proxy Server

```bash
prollama start
export OPENAI_BASE_URL=http://localhost:8741/v1
# Now every request from any OpenAI-compatible tool is anonymized automatically
```

Endpoints: `/v1/chat/completions`, `/v1/models`, `/v1/anonymize`, `/health`, `/metrics`

### Model Routing

Cost-optimized escalation: cheap model → mid → premium → top.

| Tier | Examples | When |
|------|----------|------|
| CHEAP | qwen2.5-coder:7b (local) | Typos, lint, formatting |
| MID | qwen2.5-coder:32b, DeepSeek | Bug fixes, error handling |
| PREMIUM | GPT-4o-mini, Claude Haiku | Refactors, new endpoints |
| TOP | GPT-4o, Claude Sonnet | Architecture, multi-file |

~60-80% of tasks resolve on cheap models, keeping costs minimal.

## Architecture

```
┌───────────────────────────────────────────────────┐
│                    prollama                        │
├──────────┬──────────────┬────────────┬────────────┤
│ Anonymizer│  Model Router │  Executor  │   Proxy    │
│ ┌────────┐│ ┌───────────┐│ ┌────────┐ │ ┌────────┐│
│ │ Regex  ││ │ Classify  ││ │ Solve  │ │ │ /v1/   ││
│ │ NLP    ││ │ Select    ││ │ Iterate│ │ │ chat/  ││
│ │ AST    ││ │ Escalate  ││ │ Test   │ │ │ compl. ││
│ └────────┘│ └───────────┘│ └────────┘ │ └────────┘│
└──────────┴──────────────┴────────────┴────────────┘
       ↕              ↕           ↕
   tree-sitter    LLM providers  pytest/ruff
   Presidio       (Ollama, OpenAI, Anthropic)
```

## Docker

```bash
docker compose up -d    # prollama + Ollama
```

## Development

```bash
git clone https://github.com/softreck/prollama.git
cd prollama
pip install -e ".[dev,ast]"
make test        # 124 tests
make lint        # ruff
make coverage    # pytest-cov
make check       # all of the above
```

## Project Structure

```
prollama/
├── src/prollama/
│   ├── anonymizer/           # Three-layer anonymization pipeline
│   │   ├── regex_layer.py    # Layer 1: 70+ secret/PII patterns
│   │   ├── nlp_layer.py      # Layer 2: PII in comments (heuristic/Presidio)
│   │   ├── ast_layer.py      # Layer 3: tree-sitter identifier renaming
│   │   └── pipeline.py       # Orchestrator: regex → NLP → AST
│   ├── router/
│   │   └── model_router.py   # Cost-optimized model selection + escalation
│   ├── executor/
│   │   └── task_executor.py  # Full solve loop with test validation
│   ├── cli.py                # Click CLI (8 commands)
│   ├── shell.py              # Interactive REPL (prompt-toolkit)
│   ├── proxy.py              # FastAPI OpenAI-compatible proxy
│   ├── config.py             # YAML config with Pydantic
│   └── models.py             # Domain models and enums
├── tests/                    # 124 tests across 8 test files
├── examples/                 # Sample code + runnable scripts
├── docs/                     # Full documentation (10 pages)
├── .github/workflows/ci.yml  # CI: Python 3.10-3.13 matrix
├── Dockerfile                # Container image
├── docker-compose.yml        # prollama + Ollama
├── Makefile                  # Development commands
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE                   # Apache 2.0
```

## Part of the pyqual Ecosystem

prollama is the fix provider for [pyqual](https://pyqual.dev) quality gate loops.

```yaml
# pyqual.yaml
stages:
  - name: fix
    provider: prollama
    strategy: auto
    when: metrics_fail
```

## License

Licensed under Apache-2.0.
