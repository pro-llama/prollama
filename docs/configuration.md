# Configuration

prollama is configured via `~/.prollama/config.yaml`. Generate a default config with:

```bash
prollama init
```

## Full Configuration Reference

```yaml
# ~/.prollama/config.yaml

# LLM Providers
# Add one or more providers. prollama routes requests based on the routing strategy.
providers:
  # Local provider (free, requires Ollama running)
  - name: ollama
    base_url: http://localhost:11434/v1
    models: [qwen2.5-coder:7b, qwen2.5-coder:32b]

  # OpenAI (requires API key)
  - name: openai
    api_key: ${OPENAI_API_KEY}       # reads from environment variable
    models: [gpt-4o-mini, gpt-4o]

  # Anthropic (requires API key)
  - name: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    models: [claude-sonnet-4-20250514]

  # OpenRouter (access to many models via one key)
  - name: openrouter
    api_key: ${OPENROUTER_API_KEY}
    models: [qwen/qwen3-coder-next, deepseek/deepseek-coder-v3]

# Privacy settings
privacy:
  level: full                # none | basic | full
  ast_languages:             # Languages for AST anonymization
    - python
    - javascript
    - typescript

# Model routing strategy
routing:
  strategy: cost-optimized   # cost-optimized | quality-first | local-first
  fallback: true             # Try next tier on failure

# Proxy server settings
proxy:
  host: "127.0.0.1"
  port: 8741

# Task executor settings
executor:
  max_iterations: 5          # Max retry attempts per task
  budget: 5.00               # Max USD per task
  strategy: auto             # auto | cheap | quality | local-only
```

## Privacy Levels

| Level | Layers | What's Anonymized | Performance |
|-------|--------|-------------------|-------------|
| `none` | — | Nothing | 0ms |
| `basic` | Regex | API keys, tokens, emails, IPs, connection strings | <1ms |
| `full` | Regex + NLP + AST | All of basic + person names in comments + class/function/variable names | 10-50ms |

## Routing Strategies

| Strategy | Behavior |
|----------|----------|
| `cost-optimized` | Start with cheapest model, escalate on failure (default) |
| `quality-first` | Start with premium model for all tasks |
| `local-first` | Prefer local models (Ollama), only use cloud as fallback |

## Environment Variables

prollama reads API keys from environment variables referenced in config with `${VAR_NAME}` syntax.

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `PROLLAMA_CONFIG` | Custom config file path |

## Multiple Configs

Use `--config` flag for project-specific configurations:

```bash
prollama --config ./project-prollama.yaml solve "Fix the bug"
prollama --config /etc/prollama/enterprise.yaml start
```
