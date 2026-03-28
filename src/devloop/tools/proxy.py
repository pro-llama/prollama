"""Proxy wrapper — talk to proxym without learning its API.

Usage:
    from devloop.tools.proxy import Proxy

    proxy = Proxy()                          # auto-config from env
    reply = proxy.ask("Explain this code")   # routes to best model
    reply = proxy.ask("Fix typo", tier="cheap")
    print(proxy.budget())                    # remaining budget
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from devloop.config import ProxyConfig


@dataclass
class LLMResponse:
    """Simplified LLM response."""

    content: str
    model: str = ""
    tier: str = ""
    cost_usd: float = 0.0
    elapsed_ms: float = 0.0
    raw: dict = None

    def __str__(self) -> str:
        return self.content


class Proxy:
    """Simple wrapper around proxym gateway."""

    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config or ProxyConfig.from_env()
        self._client = httpx.Client(
            base_url=self.config.url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=120.0,
        )

    def ask(
        self,
        prompt: str,
        *,
        tier: Optional[str] = None,
        model: Optional[str] = None,
        system: Optional[str] = None,
        context: bool = False,
        planfile_ref: Optional[str] = None,
        workflow_ref: Optional[str] = None,
    ) -> LLMResponse:
        """Send a prompt to the LLM via proxym.

        Args:
            prompt: Your question or instruction.
            tier: Force a tier (trivial/operational/standard/complex/deep).
            model: Force a specific model alias (cheap/balanced/premium/free/local).
            system: Optional system prompt.
            context: Inject code2llm delta context (X-Inject-Context).
            planfile_ref: Planfile ticket ref (X-Planfile-Ref: project/sprint/ticket).
            workflow_ref: Propact workflow ref (X-Workflow-Ref: workflow-id).
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {}
        if tier:
            headers["X-Task-Tier"] = tier
        if context:
            headers["X-Inject-Context"] = "true"
        if planfile_ref:
            headers["X-Planfile-Ref"] = planfile_ref
        if workflow_ref:
            headers["X-Workflow-Ref"] = workflow_ref

        body = {
            "model": model or self.config.default_tier,
            "messages": messages,
        }

        try:
            resp = self._client.post("/v1/chat/completions", json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            return LLMResponse(content=f"[proxy error: {e}]", raw={})

        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        meta = data.get("_proxy", {})
        return LLMResponse(
            content=content,
            model=meta.get("model_id", ""),
            tier=meta.get("tier", ""),
            cost_usd=meta.get("cost_usd", 0.0),
            elapsed_ms=meta.get("elapsed_ms", 0.0),
            raw=data,
        )

    def budget(self) -> dict[str, Any]:
        """Check remaining budget."""
        try:
            resp = self._client.get("/v1/budget")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return {"error": "Cannot reach proxym", "url": self.config.url}

    def models(self) -> list[dict]:
        """List available models."""
        try:
            resp = self._client.get("/v1/models")
            resp.raise_for_status()
            return resp.json().get("data", [])
        except httpx.HTTPError:
            return []

    def health(self) -> bool:
        """Check if proxym is running."""
        try:
            resp = self._client.get("/health")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
