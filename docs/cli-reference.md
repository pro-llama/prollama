# CLI Reference

## Global Options

```
prollama [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config PATH    Path to config.yaml (default: ~/.prollama/config.yaml)
  -V, --version        Show version and exit
  --help               Show help and exit
```

## Commands

### prollama init

Initialize configuration.

```bash
prollama init                    # Create default config
prollama init --provider openai  # Set default provider
```

### prollama start

Start the OpenAI-compatible proxy server.

```bash
prollama start                   # Default: 127.0.0.1:8741
prollama start --host 0.0.0.0   # Bind to all interfaces
prollama start --port 9000       # Custom port
```

Requires `prollama[proxy]`. The proxy intercepts all `/v1/chat/completions`
requests, anonymizes code, forwards to the configured provider, and rehydrates
the response.

### prollama status

Show configuration and provider status.

```bash
prollama status
```

### prollama solve

Solve a coding task using LLM orchestration.

```bash
prollama solve "Fix TypeError in auth.py"
prollama solve "Add error handling to payment module" --file src/payment.py
prollama solve "Fix the crash" --file app.py --error "TypeError: NoneType"
prollama solve "Close issue 142" --ticket github:org/repo#142
prollama solve "Refactor auth" --dry-run   # Show plan without executing
```

Options:
- `--file, -f PATH` — Source file to fix
- `--error, -e MSG` — Error message or traceback
- `--ticket, -t REF` — Ticket reference (e.g. `github:org/repo#142`)
- `--dry-run` — Show what would happen without executing

### prollama anonymize

Anonymize a source file and display results.

```bash
prollama anonymize src/payment.py
prollama anonymize src/payment.py --level full
prollama anonymize src/payment.py --level basic --output anonymized.py
```

Options:
- `--level, -l [none|basic|full]` — Privacy level (default: from config)
- `--output, -o PATH` — Write result to file instead of stdout

### prollama config

Manage configuration.

```bash
prollama config show   # Show current config as JSON
prollama config path   # Show config file path
```

### prollama shell

Start the interactive REPL. See [Shell documentation](shell.md).

```bash
prollama shell
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error / missing dependencies |
| 2 | Invalid arguments |
