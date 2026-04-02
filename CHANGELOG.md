# Changelog

All notable changes to prollama will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.7] - 2026-04-02

### Docs
- Update E2E_TEST_REPORT.md
- Update README.md
- Update README_SECURE_TOKENS.md
- Update docs/README.md

### Test
- Update test_advanced_filtering_safe.py
- Update test_comparison_safe.py
- Update test_real_projects.py
- Update test_secrets_sample_safe.py

### Other
- Update .gitignore
- Update PKG-INFO
- Update examples/workflow/auto_detection.sh
- Update examples/workflow/autodetection_demo.sh
- Update examples/workflow/autodetection_output.txt

## [0.2.6] - 2026-04-02

### Docs
- Update README.md

## [0.2.5] - 2026-04-02

### Docs
- Update README.md

## [0.2.4] - 2026-04-02

### Docs
- Update CHANGELOG.md
- Update CONTRIBUTING.md
- Update README.md
- Update docs/README.md
- Update docs/anonymization.md
- Update docs/api-reference.md
- Update docs/cli-reference.md
- Update docs/configuration.md
- Update docs/deployment.md
- Update docs/executor.md
- ... and 9 more files

### Test
- Update test_integration.sh
- Update tests/__init__.py
- Update tests/conftest.py
- Update tests/fixtures/clean_code.py
- Update tests/test_ast.py
- Update tests/test_config.py
- Update tests/test_executor.py
- Update tests/test_integration.py
- Update tests/test_nlp.py
- Update tests/test_router.py

### Other
- Update .gitignore
- Update LICENSE
- Update Makefile
- Update PKG-INFO
- Update VERSION
- Update examples/anonymize_code.py
- Update examples/batch_scan.py
- Update examples/routing_demo.py
- Update examples/sample_code/api_secrets.py
- Update examples/sample_code/fintech_app.py
- ... and 17 more files

## [0.2.3] - 2026-04-02

### Docs
- Update README.md

## [0.2.2] - 2026-04-02

### Docs
- Update README.md

## [0.2.1] - 2026-04-02

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update test_integration.sh
- Update tests/test_cli.py
- Update tests/test_config.py

### Other
- Update .gitignore
- Update VERSION
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 7 more files

## [0.1.2] - 2026-04-01

### Docs
- Update README.md

### Test
- Update tests/test_cli.py

### Other
- Update examples/sample_code/api_secrets.py
- Update examples/sample_code/ecommerce.py
- Update examples/sample_code/ml_pipeline.py

## [0.1.1] - 2026-04-01

### Docs
- Update CHANGELOG.md
- Update CONTRIBUTING.md
- Update README.md
- Update docs/anonymization.md
- Update docs/api-reference.md
- Update docs/cli-reference.md
- Update docs/configuration.md
- Update docs/deployment.md
- Update docs/executor.md
- Update docs/index.md
- ... and 6 more files

### Test
- Update tests/__init__.py
- Update tests/conftest.py
- Update tests/fixtures/clean_code.py
- Update tests/fixtures/secrets_heavy.py
- Update tests/test_ast.py
- Update tests/test_cli.py
- Update tests/test_config.py
- Update tests/test_core.py
- Update tests/test_executor.py
- Update tests/test_integration.py
- ... and 2 more files

### Other
- Update .gitignore
- Update LICENSE
- Update Makefile
- Update VERSION
- Update examples/anonymize_code.py
- Update examples/batch_scan.py
- Update examples/routing_demo.py
- Update examples/sample_code/fintech_app.py
- Update examples/sample_code/healthcare_app.py

## [0.1.0] - 2026-03-30

### Added

- **CLI** with commands: `init`, `start`, `stop`, `status`, `solve`, `anonymize`, `config`, `shell`
- **Interactive shell** with tab-completion, persistent history, Rich formatting
- **Three-layer anonymization pipeline**:
  - Layer 1: Regex — 70+ patterns for API keys, tokens, connection strings, emails, IPs (<1ms)
  - Layer 2: NLP — PII detection in comments via heuristic patterns or Presidio (optional)
  - Layer 3: AST — tree-sitter identifier renaming for Python and JavaScript (optional)
- **Reversible anonymization** — full rehydration support via stored mappings
- **Model router** with cost-optimized escalation: cheap → mid → premium → top
- **Task executor** with classify → select → anonymize → LLM call → test → iterate loop
- **OpenAI-compatible proxy** server with anonymization, rehydration, and metrics
- **Proxy endpoints**: `/v1/chat/completions`, `/v1/models`, `/v1/anonymize`, `/health`, `/metrics`
- **YAML configuration** with provider, privacy, routing, and executor settings
- **BYO Key support** — use your own API keys with zero cost for prollama
- **Local LLM support** — Ollama, vLLM, llama.cpp via OpenAI-compatible API
- **46 unit tests** covering anonymization, routing, classification, and pipeline integration
- **Python 3.10+ support** with type hints throughout
- **Apache 2.0 license**

[Unreleased]: https://github.com/softreck/prollama/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/softreck/prollama/releases/tag/v0.1.0
