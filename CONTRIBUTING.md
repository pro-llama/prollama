# Contributing to prollama

Thank you for your interest in contributing to prollama!

## Development Setup

```bash
git clone https://github.com/softreck/prollama.git
cd prollama

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev,ast]"

# Verify installation
prollama --version
make test
```

## Development Workflow

```bash
# Run tests
make test

# Run tests with coverage
make coverage

# Lint
make lint

# Format (auto-fix)
make format

# Type check
make typecheck

# Run all checks
make check
```

## Project Structure

```
src/prollama/
├── anonymizer/          # Three-layer anonymization pipeline
│   ├── regex_layer.py   # Layer 1: regex patterns for secrets/PII
│   ├── nlp_layer.py     # Layer 2: NLP-based PII detection
│   ├── ast_layer.py     # Layer 3: tree-sitter AST identifier renaming
│   └── pipeline.py      # Orchestrator: regex → NLP → AST
├── router/              # Model routing and escalation
│   └── model_router.py  # Cost-optimized model selection
├── executor/            # Task solving engine
│   └── task_executor.py # classify → select → anonymize → solve → test
├── cli.py               # Click CLI commands
├── shell.py             # Interactive REPL (prompt-toolkit)
├── proxy.py             # FastAPI OpenAI-compatible proxy
├── config.py            # YAML configuration management
└── models.py            # Pydantic domain models
```

## Adding a New Anonymization Pattern

1. Add pattern to `src/prollama/anonymizer/regex_layer.py`:

```python
SecretPattern("My Service Key", "SECRET", re.compile(r"myservice_[A-Za-z0-9]{32}")),
```

2. Add test to `tests/test_core.py`:

```python
def test_detects_my_service_key(self):
    anon = RegexAnonymizer()
    code = 'KEY = "myservice_abcdefghijklmnopqrstuvwxyz0123"'
    result, mappings = anon.anonymize(code)
    assert "myservice_" not in result
```

3. Run tests: `make test`

## Adding a New Language for AST Anonymization

1. Install the tree-sitter grammar: `pip install tree-sitter-<language>`
2. Add language targets to `ast_layer.py` `LANGUAGE_TARGETS`
3. Add builtins to `LANGUAGE_BUILTINS`
4. Add grammar loading to `ASTAnonymizer._get_language()`
5. Add tests to `tests/test_ast.py`

## Code Style

- Python 3.10+ with type hints
- Formatted with ruff (line length 100)
- Docstrings on all public functions and classes
- Tests for all new functionality

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run `make check` to verify everything passes
5. Commit with a clear message
6. Open a PR against `main`

## Reporting Issues

Please include:
- prollama version (`prollama --version`)
- Python version (`python --version`)
- OS and architecture
- Minimal reproduction steps
- Expected vs actual behavior
