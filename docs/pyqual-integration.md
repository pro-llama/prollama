# pyqual Integration

prollama is the native fix provider for [pyqual](https://pyqual.dev) quality gate loops.
When pyqual detects that code fails quality metrics, prollama automatically generates fixes.

## Setup

```yaml
# pyqual.yaml
pipeline:
  name: quality-loop

  metrics:
    cc_max: 15
    vallm_pass_min: 90
    coverage_min: 80

  stages:
    - name: analyze
      run: code2llm ./ -f toon,evolution

    - name: validate
      run: vallm batch ./ --recursive

    - name: fix
      provider: prollama
      strategy: auto
      when: metrics_fail

    - name: test
      run: pytest --cov

  loop:
    max_iterations: 3
    on_fail: report
```

## How It Works

1. pyqual runs the `analyze` and `validate` stages
2. If metrics fail, pyqual invokes prollama as the fix provider
3. prollama receives the failing metrics and source code
4. prollama anonymizes the code, selects a model, generates a fix
5. pyqual runs `test` to verify the fix
6. If tests pass and metrics improve, the loop ends
7. If not, pyqual triggers another iteration (up to `max_iterations`)

## Strategy Options

| Strategy | Behavior |
|----------|----------|
| `auto` | prollama selects model based on task complexity (default) |
| `cheap` | Always use cheapest model — slower but lowest cost |
| `quality` | Always use premium model — faster but higher cost |
| `local-only` | Only use local models — zero data in cloud |

## CLI Integration

```bash
# Run pyqual with prollama as fix provider
pyqual run

# Or invoke prollama directly with a pyqual report
prollama solve --pyqual-report .pyqual/report.json
```

## GitHub Actions

```yaml
# .github/workflows/quality.yml
name: Quality Gate
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pyqual prollama
      - run: pyqual run
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Ecosystem

prollama works with the full pyqual ecosystem:

- **code2llm** — generates code analysis metrics
- **vallm** — validates code quality via LLM
- **prollama** — fixes code that fails quality gates
- **planfile** — manages tickets and tasks
- **costs** — tracks LLM costs across tools
