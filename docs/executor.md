# Task Executor

The Task Executor is prollama's core engine. It takes a task description, orchestrates
the full solve loop, and returns a validated fix.

## The Solve Loop

```
1. CLASSIFY    — determine complexity (simple/medium/hard/very_hard) and type (fix/refactor/feature)
2. SELECT      — pick starting model via router (cheapest adequate tier)
3. CONTEXT     — gather relevant code, error traces, file contents
4. ANONYMIZE   — strip secrets, PII, and business identifiers
5. CALL LLM    — send anonymized context + task to the selected model
6. REHYDRATE   — restore original names in LLM response
7. TEST        — run project tests (pytest) against the fix
8. ITERATE     — if tests fail, adjust strategy or escalate model (up to max_iterations)
9. DELIVER     — return patch, cost, timing, and model info
```

## Usage

### CLI

```bash
prollama solve "Fix the TypeError in payment.py" --file src/payment.py
```

### Python API

```python
from prollama.config import Config
from prollama.executor import TaskExecutor
from prollama.models import Task

config = Config.load()
executor = TaskExecutor(config)

task = Task(
    description="Fix race condition in queue processor",
    file_path="src/queue.py",
    error="RuntimeError: coroutine was never awaited",
)

result = executor.solve(task)

if result.status.value == "completed":
    print(f"Fixed in {result.iterations} iterations")
    print(f"Model: {result.model_used}")
    print(f"Cost: ${result.cost_usd:.4f}")
    print(result.patch)
else:
    print(f"Failed: {result.error_message}")
```

## Escalation Behavior

When a model fails to produce a working fix:

1. **Iteration 1-2**: Retry with the same model (different prompt approach)
2. **Iteration 3+**: Escalate to the next tier model
3. **Max iterations reached**: Report failure with details

The executor tracks cost across all iterations. Even if escalation occurs,
total cost stays within the configured budget (`executor.budget` in config).

## Task Types

| Type | Description | Typical Models |
|------|-------------|---------------|
| FIX | Bug fixes, error handling | CHEAP → MID |
| REFACTOR | Code restructuring | MID → PREMIUM |
| FEATURE | New functionality | PREMIUM → TOP |
| SECURITY | Vulnerability patches | PREMIUM → TOP (dedicated pipeline) |
| TEST | Test generation | CHEAP → MID |

## Configuration

```yaml
executor:
  max_iterations: 5    # Max attempts before giving up
  budget: 5.00         # Max USD per task
  strategy: auto       # auto | cheap | quality | local-only
```

## Integration with pyqual

When used as a pyqual fix provider, the executor receives failing quality metrics
and generates fixes that satisfy the quality gates:

```yaml
# pyqual.yaml
stages:
  - name: fix
    provider: prollama
    strategy: auto
    when: metrics_fail
```

See [pyqual Integration](pyqual-integration.md) for details.
