# Quickstart

Get prollama running and solve your first task in 60 seconds.

## Install

```bash
pip install prollama
```

With optional AST anonymization (recommended):

```bash
pip install prollama[ast]
```

## Initialize

```bash
prollama init
```

This creates `~/.prollama/config.yaml` with default settings pointing to a local
Ollama instance. Edit the file to add cloud providers if needed.

## Verify

```bash
prollama status
```

Shows your configuration, providers, and current settings.

## Solve a Task

```bash
prollama solve "Fix the TypeError in auth.py line 42" --file src/auth.py
```

Or use dry-run to see what prollama would do without executing:

```bash
prollama solve "Refactor user service to use dependency injection" --dry-run
```

## Anonymize a File

```bash
# Basic — regex only (secrets, API keys, emails)
prollama anonymize src/payment.py --level basic

# Full — regex + NLP + AST (all business logic hidden)
prollama anonymize src/payment.py --level full
```

## Interactive Shell

```bash
prollama shell
```

Inside the shell:

```
prollama ▸ solve "Add type hints to utils.py" --file src/utils.py
prollama ▸ models
prollama ▸ history
prollama ▸ cost
```

## Start as Proxy

```bash
pip install prollama[proxy]
prollama start
```

Then configure your IDE:

```bash
export OPENAI_BASE_URL=http://localhost:8741/v1
```

Every request through the proxy is automatically anonymized and rehydrated.

## Use with Docker

```bash
docker compose up -d    # starts prollama + Ollama
```

## Next Steps

- [Configuration](configuration.md) — add cloud providers, tune privacy
- [Anonymization](anonymization.md) — understand the three layers
- [pyqual Integration](pyqual-integration.md) — use prollama in quality gate loops
