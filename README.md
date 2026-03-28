# Prollama

Progressive algorithmization toolchain — from LLM to deterministic code, from proxy to tickets.

## Overview

Prollama is a comprehensive Python package that provides tools for:
- **LLM Integration**: Chat with various language models (OpenAI, etc.)
- **Proxy Management**: HTTP proxy operations and testing
- **Ticket Management**: Create and manage tickets across different providers (GitHub, etc.)
- **Configuration Management**: YAML-based configuration system
- **CLI Interface**: Command-line tools for all operations

## Installation

```bash
pip install prollama
```

For development with all optional dependencies:

```bash
pip install prollama[all]
```

## Quick Start

### 1. Initialize Configuration

```bash
prollama config llm.provider openai
prollama config llm.api_key your_openai_api_key
prollama config llm.model gpt-3.5-turbo
```

### 2. Chat with LLM

```bash
prollama chat "Hello, how are you?"
prollama chat "Explain quantum computing" --system "You are a physics expert"
```

### 3. Test Proxy

```bash
prollama config proxy.enabled true
prollama config proxy.host localhost
prollama config proxy.port 8080
prollama proxy-test
```

### 4. Manage Tickets

```bash
# Configure GitHub integration
prollama config tickets.provider github
prollama config tickets.token your_github_token
prollama config tickets.repo owner/repo

# List tickets
prollama ticket-list

# Create a ticket
prollama ticket-create "Bug in authentication" --description "Users cannot login with OAuth2"
```

## Python API

### Core Usage

```python
from prollama import ProllamaCore, LLMInterface, ProxyManager, TicketManager

# Initialize core with configuration
core = ProllamaCore("config.yaml")

# LLM Interface
llm = LLMInterface(
    provider="openai",
    api_key="your_api_key",
    model="gpt-3.5-turbo"
)
response = llm.simple_chat("Hello, world!")
print(response)

# Proxy Manager
proxy_manager = ProxyManager()
success = proxy_manager.test_proxy()

# Ticket Manager
ticket_manager = TicketManager(
    provider="github",
    token="your_github_token",
    repo="owner/repo"
)
tickets = ticket_manager.list_tickets()
```

### Configuration

Create a `prollama.yaml` file:

```yaml
llm:
  provider: openai
  model: gpt-3.5-turbo
  api_key: ${OPENAI_API_KEY}

proxy:
  enabled: false
  host: localhost
  port: 8080

tickets:
  provider: github
  token: ${GITHUB_TOKEN}
  repo: owner/repo
```

## CLI Commands

### Configuration

```bash
# Show all configuration
prollama config

# Get specific value
prollama config llm.model

# Set configuration value
prollama config llm.model gpt-4
```

### LLM Chat

```bash
# Simple chat
prollama chat "Your prompt here"

# With system prompt and custom model
prollama chat "Explain AI" --system "You are an AI expert" --model gpt-4
```

### Proxy Operations

```bash
# Test proxy connectivity
prollama proxy-test

# Configure proxy
prollama config proxy.enabled true
prollama config proxy.host proxy.example.com
prollama config proxy.port 3128
```

### Ticket Management

```bash
# List open tickets
prollama ticket-list

# List closed tickets
prollama ticket-list --status closed

# Create new ticket
prollama ticket-create "New feature request" \
  --description "Add support for dark mode" \
  --labels "enhancement,ui" \
  --priority high
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/semcod/devloop.git
cd devloop

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Lint code
ruff check .
ruff format .

# Type checking
mypy src/
```

### Project Structure

```
src/prollama/
├── __init__.py      # Package initialization
├── core.py         # Core configuration and utilities
├── llm.py          # LLM interface
├── proxy.py        # Proxy management
├── tickets.py      # Ticket management
└── cli.py          # Command-line interface
```

## License

Licensed under Apache-2.0.


Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

- Documentation: [GitHub Wiki](https://github.com/semcod/devloop/wiki)
- Issues: [GitHub Issues](https://github.com/semcod/devloop/issues)
- Discussions: [GitHub Discussions](https://github.com/semcod/devloop/discussions)
