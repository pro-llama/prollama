"""
LLM interface for Prollama
"""

import os

import httpx
import requests
from pydantic import BaseModel, Field
from rich.console import Console

from prollama.config import ProviderConfig

console = Console()


class Message(BaseModel):
    """Message model for LLM interactions"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class LLMResponse(BaseModel):
    """Response model for LLM"""
    content: str = Field(..., description="Response content")
    usage: dict[str, int] = Field(default_factory=dict, description="Token usage info")
    model: str = Field(..., description="Model used")


class LLMInterface:
    """Interface for interacting with LLM providers"""

    def __init__(self, provider: str = "openai", api_key: str | None = None, model: str = "gpt-3.5-turbo"):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client()

    def chat(self, messages: list[Message], **kwargs) -> LLMResponse:
        """Send chat completion request"""
        if self.provider == "openai":
            return self._openai_chat(messages, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _openai_chat(self, messages: list[Message], **kwargs) -> LLMResponse:
        """OpenAI chat completion"""
        if not self.api_key:
            raise ValueError("API key is required for OpenAI")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [msg.model_dump() for msg in messages],
            **kwargs
        }

        try:
            response = self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()

            result = response.json()
            choice = result["choices"][0]

            return LLMResponse(
                content=choice["message"]["content"],
                usage=result.get("usage", {}),
                model=result["model"]
            )
        except Exception as e:
            console.print(f"[red]✗[/red] LLM request failed: {e}")
            raise

    def simple_chat(self, prompt: str, system_prompt: str | None = None) -> str:
        """Simple chat interface"""
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))

        response = self.chat(messages)
        return response.content

    def close(self):
        """Close HTTP client"""
        self.client.close()


class LLMClient:
    """Client for interacting with LLM providers (matches test API)."""

    def __init__(self, provider: ProviderConfig):
        self.provider = provider
        if not self.provider.api_key:
            raise ValueError("API key is required")

    def resolve_api_key(self) -> str | None:
        """Expand $ENV_VAR references in api_key."""
        return self.provider.resolve_api_key()

    def complete(self, prompt: str, model: str | None = None) -> str:
        """Send a simple completion request and return the response text."""
        api_key = self.resolve_api_key()
        if not api_key:
            raise ValueError("API key is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model or (self.provider.models[0] if self.provider.models else "gpt-3.5-turbo"),
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            f"{self.provider.base_url or 'https://api.openai.com/v1'}/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def list_models(self) -> list[str]:
        """Return list of available models for this provider."""
        return self.provider.models
