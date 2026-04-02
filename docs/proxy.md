# Proxy Server

prollama runs as an OpenAI-compatible proxy that sits between your tools and any LLM provider.
Every request is automatically anonymized before leaving your machine.

## Starting the Proxy

```bash
pip install prollama[proxy]
prollama start
```

Default: `http://127.0.0.1:8741`. Override with `--host` and `--port`.

## Connecting Your Tools

Set one environment variable — every OpenAI-compatible tool works automatically:

```bash
export OPENAI_BASE_URL=http://localhost:8741/v1
```

Works with: VS Code Copilot Chat, Continue.dev, Aider, any OpenAI SDK client.

## Endpoints

### POST /v1/chat/completions

Standard OpenAI chat completions endpoint. prollama:

1. Intercepts the request
2. Anonymizes all message contents (regex + NLP + AST based on privacy level)
3. Forwards to the configured provider
4. Rehydrates the response (restores original identifiers)
5. Returns the response with a `prollama` metadata block

Response includes extra metadata:

```json
{
  "choices": [...],
  "usage": {...},
  "prollama": {
    "anonymized_items": 12,
    "privacy_level": "full",
    "estimated_cost_usd": 0.003,
    "provider": "ollama"
  }
}
```

### GET /v1/models

Lists all available models across configured providers:

```bash
curl http://localhost:8741/v1/models | jq
```

### POST /v1/anonymize

Preview anonymization without sending anything to an LLM:

```bash
curl -X POST http://localhost:8741/v1/anonymize \
  -H "Content-Type: application/json" \
  -d '{"code": "API_KEY = \"sk_live_xxx\"", "language": "python"}'
```

Returns:

```json
{
  "anonymized": "API_KEY = \"[SECRET_001]\"",
  "stats": {"SECRET": 1},
  "privacy_level": "full",
  "mappings_count": 1
}
```

### GET /health

Health check with configuration summary.

### GET /metrics

Request and cost metrics for the current session:

```json
{
  "total_requests": 47,
  "total_tokens": {"input": 125000, "output": 43000},
  "total_cost_usd": 0.82,
  "total_anonymized_items": 312,
  "errors": 2
}
```

## Docker Deployment

```bash
docker compose up -d
```

This starts prollama + Ollama. The proxy is available at `localhost:8741`,
Ollama at `localhost:11434`.

For production, bind to a specific network interface:

```bash
prollama start --host 10.0.0.5 --port 8741
```

## Limitations

- Streaming (`stream: true`) is not yet supported. Set `stream: false` in requests.
- Function calling / tool use is proxied as-is (no anonymization of tool arguments yet).
- File/image content in multimodal requests is passed through without anonymization.
