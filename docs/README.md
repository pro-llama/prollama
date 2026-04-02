<!-- code2docs:start --># prollama

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-142-green)
> **142** functions | **45** classes | **28** files | CC̄ = 3.1

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/pro-llama/prollama](https://github.com/pro-llama/prollama)

## Installation

### From PyPI

```bash
pip install prollama
```

### From Source

```bash
git clone https://github.com/pro-llama/prollama
cd prollama
pip install -e .
```

### Optional Extras

```bash
pip install prollama[nlp]    # nlp features
pip install prollama[ast]    # ast features
pip install prollama[proxy]    # proxy features
pip install prollama[all]    # all optional features
pip install prollama[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
prollama ./my-project

# Only regenerate README
prollama ./my-project --readme-only

# Preview what would be generated (no file writes)
prollama ./my-project --dry-run

# Check documentation health
prollama check ./my-project

# Sync — regenerate only changed modules
prollama sync ./my-project
```

### Python API

```python
from prollama import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `prollama`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `prollama.yaml` in your project root (or run `prollama init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

prollama can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- prollama:start -->
# Project Title
... auto-generated content ...
<!-- prollama:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
prollama/
├── project    ├── routing_demo        ├── ml_pipeline    ├── anonymize_code        ├── healthcare_app        ├── ecommerce        ├── api_secrets    ├── batch_scan        ├── fintech_app        ├── proxy    ├── prollama/        ├── cli        ├── __main__        ├── shell        ├── models        ├── core            ├── nlp_layer            ├── ast_layer        ├── anonymizer/            ├── regex_layer            ├── pipeline        ├── executor/        ├── config            ├── task_executor        ├── router/            ├── model_router        ├── llm        ├── tickets```

## API Overview

### Classes

- **`MLModelManager`** — Manages ML model lifecycle including training and deployment.
- **`InferenceService`** — Real-time inference service for deployed models.
- **`PatientRecordService`** — Manages electronic health records (EHR) for MedTech Solutions.
- **`MedTechBillingProcessor`** — Insurance billing for MedTech Solutions.
- **`PaymentGateway`** — Unified payment gateway supporting multiple providers.
- **`ShippingManager`** — Manages shipping calculations and label generation.
- **`NotificationService`** — Handles customer notifications via multiple channels.
- **`APIClientManager`** — Manages multiple API clients with secure authentication.
- **`WebhookHandler`** — Handles incoming webhooks from external services.
- **`AcmePaymentProcessor`** — Handles all payment processing for Acme Fintech premium customers.
- **`AcmeSubscriptionManager`** — Manages recurring subscriptions for Acme Fintech.
- **`RequestMetric`** — —
- **`MetricsCollector`** — —
- **`ProllamaShell`** — Interactive REPL for prollama.
- **`TaskComplexity`** — —
- **`TaskType`** — —
- **`TaskStatus`** — —
- **`PrivacyLevel`** — —
- **`ModelTier`** — —
- **`AnonymizationMapping`** — Tracks original ↔ anonymized token pairs for rehydration.
- **`AnonymizationResult`** — Output of the anonymization pipeline.
- **`Task`** — A unit of work submitted to the executor.
- **`TaskResult`** — Result of a completed (or failed) task.
- **`ProxyRequest`** — Incoming chat completion request (OpenAI-compatible subset).
- **`ProllamaCore`** — Main core class for Prollama functionality
- **`NLPAnonymizer`** — Detect and anonymize PII in code comments and string literals.
- **`ASTAnonymizer`** — Anonymize identifiers in source code using tree-sitter AST parsing.
- **`SecretPattern`** — —
- **`RegexAnonymizer`** — Apply regex-based anonymization to source code text.
- **`AnonymizationPipeline`** — Orchestrate the anonymization layers according to privacy level.
- **`ProviderConfig`** — —
- **`PrivacyConfig`** — —
- **`RoutingConfig`** — —
- **`ProxyConfig`** — —
- **`ExecutorConfig`** — —
- **`Config`** — Root configuration for prollama.
- **`TaskExecutor`** — Orchestrate the full task-solving loop.
- **`ModelInfo`** — —
- **`ModelRouter`** — Select and escalate models based on task complexity and strategy.
- **`Message`** — Message model for LLM interactions
- **`LLMResponse`** — Response model for LLM
- **`LLMInterface`** — Interface for interacting with LLM providers
- **`Ticket`** — Ticket model for issue tracking
- **`TicketCreate`** — Ticket creation model
- **`TicketManager`** — Manager for ticket operations across different providers

### Functions

- `demo_routing()` — Demonstrate model selection and escalation.
- `anonymize_and_compare(file_path, level)` — Anonymize a file and display a comparison of original vs anonymized.
- `main()` — —
- `scan_project(directory, level)` — Scan a project directory and report all sensitive items found.
- `main()` — —
- `create_app(config)` — Create the FastAPI proxy application.
- `main(ctx, config_path, version)` — prollama — Intelligent LLM Execution Layer for developer teams.
- `init(ctx, provider)` — Initialize prollama configuration.
- `start(ctx, host, port)` — Start the prollama proxy server.
- `stop()` — Stop the prollama proxy server.
- `status(ctx)` — Show prollama status and configuration.
- `solve(ctx, description, file_path, error)` — Solve a coding task using LLM orchestration.
- `anonymize(ctx, file_path, level, output)` — Anonymize a source file and show results.
- `config_group()` — Manage prollama configuration.
- `config_show(ctx)` — Show current configuration.
- `config_path()` — Show config file path.
- `shell(ctx)` — Start interactive prollama shell.
- `classify_complexity(task)` — Simple heuristic classifier based on description keywords.
- `classify_type(task)` — Heuristic task-type classifier.


## Project Structure

📄 `examples.anonymize_code` (2 functions)
📄 `examples.batch_scan` (2 functions)
📄 `examples.routing_demo` (1 functions)
📄 `examples.sample_code.api_secrets` (8 functions, 2 classes)
📄 `examples.sample_code.ecommerce` (11 functions, 3 classes)
📄 `examples.sample_code.fintech_app` (7 functions, 2 classes)
📄 `examples.sample_code.healthcare_app` (5 functions, 2 classes)
📄 `examples.sample_code.ml_pipeline` (8 functions, 2 classes)
📄 `project`
📦 `src.prollama`
📄 `src.prollama.__main__`
📦 `src.prollama.anonymizer`
📄 `src.prollama.anonymizer.ast_layer` (9 functions, 1 classes)
📄 `src.prollama.anonymizer.nlp_layer` (7 functions, 1 classes)
📄 `src.prollama.anonymizer.pipeline` (5 functions, 1 classes)
📄 `src.prollama.anonymizer.regex_layer` (5 functions, 2 classes)
📄 `src.prollama.cli` (13 functions)
📄 `src.prollama.config` (6 functions, 6 classes)
📄 `src.prollama.core` (6 functions, 1 classes)
📦 `src.prollama.executor`
📄 `src.prollama.executor.task_executor` (9 functions, 1 classes)
📄 `src.prollama.llm` (5 functions, 3 classes)
📄 `src.prollama.models` (10 classes)
📄 `src.prollama.proxy` (5 functions, 2 classes)
📦 `src.prollama.router`
📄 `src.prollama.router.model_router` (5 functions, 2 classes)
📄 `src.prollama.shell` (15 functions, 1 classes)
📄 `src.prollama.tickets` (8 functions, 3 classes)

## Requirements

- Python >= >=3.10
- click >=8.1- rich >=13.0- prompt-toolkit >=3.0- pyyaml >=6.0- httpx >=0.27- pydantic >=2.0- pydantic-settings >=2.0- python-dotenv >=1.0- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/pro-llama/prollama
cd prollama

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/pro-llama/prollama/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/pro-llama/prollama/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/pro-llama/prollama/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/pro-llama/prollama/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->