"""OpenAI-compatible proxy server with anonymization and metrics.

Provides:
  - POST /v1/chat/completions  — proxied with anonymization + rehydration
  - GET  /v1/models            — list available models from all providers
  - POST /v1/anonymize         — preview anonymization without sending to LLM
  - GET  /health               — health check
  - GET  /metrics              — request and cost metrics

Requires: pip install prollama[proxy]
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from prollama.config import Config

# ---------------------------------------------------------------------------
# Metrics collector
# ---------------------------------------------------------------------------

@dataclass
class RequestMetric:
    timestamp: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    anonymized_count: int
    duration_ms: float
    status: str


@dataclass
class MetricsCollector:
    requests: list[RequestMetric] = field(default_factory=list)
    total_requests: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost: float = 0.0
    total_anonymized: int = 0
    errors: int = 0

    def record(self, metric: RequestMetric) -> None:
        self.requests.append(metric)
        if len(self.requests) > 1000:
            self.requests = self.requests[-500:]
        self.total_requests += 1
        self.total_tokens_in += metric.input_tokens
        self.total_tokens_out += metric.output_tokens
        self.total_cost += metric.cost_usd
        self.total_anonymized += metric.anonymized_count
        if metric.status != "ok":
            self.errors += 1

    def summary(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "total_tokens": {
                "input": self.total_tokens_in,
                "output": self.total_tokens_out,
            },
            "total_cost_usd": round(self.total_cost, 6),
            "total_anonymized_items": self.total_anonymized,
            "errors": self.errors,
            "recent_requests": len(self.requests),
        }


class Proxy:
    """Proxy server wrapper that matches test API expectations."""

    def __init__(self, config: Config):
        self.config = config
        self._app = None

    def get_app(self):
        """Get or create the FastAPI application."""
        if self._app is None:
            self._app = create_app(self.config)
        return self._app


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(config: Config):
    """Create the FastAPI proxy application."""
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    from prollama import __version__
    from prollama.anonymizer.pipeline import AnonymizationPipeline
    from prollama.models import PrivacyLevel
    from prollama.router.model_router import ModelRouter

    app = FastAPI(
        title="prollama proxy",
        version=__version__,
        description="OpenAI-compatible proxy with code anonymization",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    pipeline = AnonymizationPipeline(
        privacy_level=PrivacyLevel(config.privacy.level),
    )
    model_router = ModelRouter(config=config)
    metrics = MetricsCollector()

    # -- health -------------------------------------------------------------

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "version": __version__,
            "privacy_level": config.privacy.level,
            "routing_strategy": config.routing.strategy,
            "providers": config.provider_names(),
        }

    # -- metrics ------------------------------------------------------------

    @app.get("/metrics")
    async def get_metrics():
        return metrics.summary()

    # -- list models --------------------------------------------------------

    @app.get("/v1/models")
    async def list_models():
        """OpenAI-compatible model listing."""
        available = model_router.available_models()
        model_list = [
            {
                "id": m.name,
                "object": "model",
                "created": 0,
                "owned_by": m.provider,
            }
            for m in available
        ]
        return {"object": "list", "data": model_list}

    # -- chat completions ---------------------------------------------------

    @app.post("/v1/chat/completions")
    async def chat_completions(http_request: Request):
        """Proxy /v1/chat/completions with anonymization + rehydration."""
        import httpx

        t0 = time.monotonic()
        body = await http_request.json()
        model_name = body.get("model", "")
        messages = body.get("messages", [])

        if body.get("stream", False):
            return JSONResponse(
                {"error": {"message": "Streaming not yet supported. Set stream=false.", "type": "invalid_request"}},
                status_code=400,
            )

        # Anonymize message contents
        all_mappings = []
        anon_messages = []
        anonymized_count = 0

        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                result = pipeline.run(content)
                anon_messages.append({**msg, "content": result.anonymized_code})
                all_mappings.extend(result.mappings)
                anonymized_count += len(result.mappings)
            else:
                anon_messages.append(msg)

        body["messages"] = anon_messages

        # Resolve provider
        provider = _resolve_provider(config, model_name)
        if provider is None:
            _record_error(metrics, model_name, "unknown", anonymized_count, t0, "error_no_provider")
            return JSONResponse(
                {"error": {"message": f"No provider for model '{model_name}'", "type": "invalid_request"}},
                status_code=400,
            )

        base_url = provider.base_url or "http://localhost:11434/v1"
        api_key = provider.resolve_api_key() or ""

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Forward to provider
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{base_url}/chat/completions", json=body, headers=headers)
            resp_data = resp.json()
        except httpx.ConnectError:
            _record_error(metrics, model_name, provider.name, anonymized_count, t0, "error_connection")
            return JSONResponse(
                {"error": {"message": f"Cannot connect to {provider.name} at {base_url}", "type": "connection_error"}},
                status_code=502,
            )
        except Exception as exc:
            _record_error(metrics, model_name, provider.name, anonymized_count, t0, f"error_{type(exc).__name__}")
            return JSONResponse(
                {"error": {"message": str(exc), "type": "proxy_error"}},
                status_code=502,
            )

        # Rehydrate response
        if "choices" in resp_data:
            for choice in resp_data["choices"]:
                content = choice.get("message", {}).get("content", "")
                if content and all_mappings:
                    choice["message"]["content"] = pipeline.rehydrate(content, all_mappings)

        # Extract usage
        usage = resp_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Estimate cost
        model_info = next((m for m in model_router.available_models() if m.name == model_name), None)
        cost = model_router.estimate_cost(model_info, input_tokens, output_tokens) if model_info else 0.0

        # Inject prollama metadata
        resp_data["prollama"] = {
            "anonymized_items": anonymized_count,
            "privacy_level": config.privacy.level,
            "estimated_cost_usd": round(cost, 6),
            "provider": provider.name,
        }

        duration_ms = round((time.monotonic() - t0) * 1000, 1)
        metrics.record(RequestMetric(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=model_name,
            provider=provider.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            anonymized_count=anonymized_count,
            duration_ms=duration_ms,
            status="ok",
        ))

        return JSONResponse(resp_data, status_code=resp.status_code)

    # -- anonymize preview --------------------------------------------------

    @app.post("/v1/anonymize")
    async def anonymize_preview(http_request: Request):
        """Preview anonymization without sending to any LLM."""
        body = await http_request.json()
        code = body.get("code", "")
        language = body.get("language", "python")

        result = pipeline.run(code, language=language)

        return {
            "anonymized": result.anonymized_code,
            "stats": result.stats,
            "privacy_level": result.privacy_level.value,
            "mappings_count": len(result.mappings),
        }

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_provider(config: Config, model: str):
    """Find the provider that serves a given model name."""
    for p in config.providers:
        if model in p.models:
            return p
    for p in config.providers:
        if not p.models:
            return p
    return config.providers[0] if config.providers else None


def _record_error(
    metrics: MetricsCollector,
    model: str,
    provider: str,
    anonymized_count: int,
    t0: float,
    status: str,
) -> None:
    metrics.record(RequestMetric(
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=model,
        provider=provider,
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        anonymized_count=anonymized_count,
        duration_ms=round((time.monotonic() - t0) * 1000, 1),
        status=status,
    ))
