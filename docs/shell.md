# Interactive Shell

The prollama shell is a REPL for interactive task solving, code anonymization,
and session management.

## Starting the Shell

```bash
prollama shell
```

## Features

- **Tab-completion** for all commands and flags
- **Persistent history** stored in `~/.prollama/shell_history`
- **Auto-suggest** from history (press → to accept)
- **Rich formatting** with colored output, tables, and panels
- **Implicit solve** — type any text without a command prefix to treat it as a task

## Commands

| Command | Description |
|---------|-------------|
| `solve <desc> [flags]` | Solve a coding task |
| `anonymize <file>` | Anonymize a source file |
| `status` | Session and config status |
| `providers` | List configured LLM providers |
| `models` | List available models with costs |
| `config` | Show full config as JSON |
| `history` | Task history for this session |
| `cost` | Accumulated session cost |
| `clear` | Clear terminal |
| `help` | Show command reference |
| `exit` / `quit` | Exit shell |

## Solve Command

```
prollama ▸ solve "Fix the TypeError in auth.py" --file src/auth.py --error "TypeError: NoneType"
```

Flags:
- `--file <path>` — Source file to work on
- `--error <msg>` — Error message or traceback
- `--ticket <ref>` — Ticket reference
- `--dry-run` — Show plan without executing

## Implicit Solve

Anything not recognized as a command is treated as a solve description:

```
prollama ▸ Fix all mypy errors in src/
```

Is equivalent to:

```
prollama ▸ solve "Fix all mypy errors in src/"
```

## Session Tracking

The shell tracks all tasks solved during the session:

```
prollama ▸ history
  # │ Status │ Model            │ Iter │ Time  │ Cost
  1 │ ✓      │ qwen2.5-coder:7b │ 1    │ 2.3s  │ $0.0000
  2 │ ✓      │ qwen2.5-coder:32b│ 3    │ 12.1s │ $0.0000
  3 │ ✗      │ gpt-4o-mini      │ 5    │ 45.8s │ $0.0032

  Total cost: $0.0032

prollama ▸ cost
  Session tasks: 3
  Total cost: $0.0032
```
