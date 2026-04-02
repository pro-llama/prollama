"""Configuration loading and management for prollama.

Loads from (priority order):
1. Environment variables (PROLLAMA_* and standard names)
2. .env file in project root or current directory
3. ~/.prollama/config.yaml
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

# Load .env file if present
from dotenv import load_dotenv

# Try loading from multiple locations
_env_loaded = False
for _env_path in [
    Path("/home/tom/github/pro-llama/.env"),  # Shared ecosystem config
    Path.home() / ".prollama" / ".env",       # User-level config
    Path.cwd() / ".env",                      # Project-level config
]:
    if _env_path.exists():
        load_dotenv(_env_path, override=False)
        _env_loaded = True
        break

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_DIR = Path.home() / ".prollama"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_PROXY_HOST = "127.0.0.1"
DEFAULT_PROXY_PORT = 8741

DEFAULT_CONFIG_TEMPLATE = """\
# prollama configuration
# Docs: https://docs.prollama.dev/config

providers:
  - name: ollama
    base_url: http://localhost:11434/v1
    models: [qwen2.5-coder:7b]

  # Uncomment to add cloud providers:
  # - name: openai
  #   api_key: ${OPENAI_API_KEY}
  #   models: [gpt-4o-mini, gpt-4o]
  #
  # - name: anthropic
  #   api_key: ${ANTHROPIC_API_KEY}
  #   models: [claude-sonnet-4-20250514]

privacy:
  level: full          # none | basic | full
  ast_languages: [python, javascript, typescript]

routing:
  strategy: cost-optimized   # cost-optimized | quality-first | local-first
  fallback: true

proxy:
  host: "127.0.0.1"
  port: 8741

executor:
  max_iterations: 5
  budget: 5.00
  strategy: auto       # auto | cheap | quality | local-only
"""


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ProviderConfig(BaseModel):
    name: str
    base_url: str | None = None
    api_key: str | None = None
    models: list[str] = Field(default_factory=list)

    def resolve_api_key(self) -> str | None:
        """Expand $ENV_VAR references in api_key."""
        if self.api_key and self.api_key.startswith("${") and self.api_key.endswith("}"):
            env_var = self.api_key[2:-1]
            return os.environ.get(env_var)
        return self.api_key


class PrivacyConfig(BaseModel):
    level: str = "full"  # none | basic | full
    ast_languages: list[str] = Field(default_factory=lambda: ["python"])


class RoutingConfig(BaseModel):
    strategy: str = "cost-optimized"
    fallback: bool = True


class ProxyConfig(BaseModel):
    host: str = DEFAULT_PROXY_HOST
    port: int = DEFAULT_PROXY_PORT


class ExecutorConfig(BaseModel):
    max_iterations: int = 5
    budget: float = 5.00
    strategy: str = "auto"
    llm_model: str | None = None  # Preferred model from LLM_MODEL env var
    llm_fallback_model: str | None = None  # Fallback model from LLM_FALLBACK_MODEL env var


class Config(BaseModel):
    """Root configuration for prollama."""

    debug: bool = False
    providers: list[ProviderConfig] = Field(default_factory=list)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)

    # -- I/O helpers --------------------------------------------------------

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Load config from YAML, .env, and environment variables.
        
        Priority: env vars > .env file > config.yaml > defaults
        """
        path = path or DEFAULT_CONFIG_FILE
        
        # Start with defaults or YAML config
        if path.exists():
            raw = yaml.safe_load(path.read_text()) or {}
            config = cls(**raw)
        else:
            config = cls()
        
        # Override with environment variables (standardized naming)
        # Proxy settings
        if proxy_host := os.getenv("PROXY_HOST"):
            config.proxy.host = proxy_host
        if proxy_port := os.getenv("PROXY_PORT"):
            config.proxy.port = int(proxy_port)
        
        # Privacy settings
        if privacy_level := os.getenv("ANONYMIZER_LEVEL"):
            config.privacy.level = privacy_level
        if privacy_langs := os.getenv("ANONYMIZER_LANGUAGES"):
            config.privacy.ast_languages = privacy_langs.split(",")
        
        # Routing settings
        if routing_strategy := os.getenv("ROUTING_STRATEGY"):
            config.routing.strategy = routing_strategy
        if os.getenv("ROUTING_FALLBACK", "").lower() in ("true", "1", "yes"):
            config.routing.fallback = True
        elif os.getenv("ROUTING_FALLBACK", "").lower() in ("false", "0", "no"):
            config.routing.fallback = False
        
        # Executor settings
        if max_iter := os.getenv("EXECUTOR_MAX_ITERATIONS"):
            config.executor.max_iterations = int(max_iter)
        if budget := os.getenv("EXECUTOR_BUDGET_USD"):
            config.executor.budget = float(budget)
        if exec_strategy := os.getenv("EXECUTOR_STRATEGY"):
            config.executor.strategy = exec_strategy
        if llm_model := os.getenv("LLM_MODEL"):
            config.executor.llm_model = llm_model
        if llm_fallback := os.getenv("LLM_FALLBACK_MODEL"):
            config.executor.llm_fallback_model = llm_fallback
        
        # API Keys for providers (from standardized env vars)
        api_keys = {
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        }
        
        # Add providers from env if API keys present
        for provider_name, api_key in api_keys.items():
            if api_key:
                existing = config.get_provider(provider_name)
                if existing:
                    existing.api_key = api_key
                else:
                    config.providers.append(ProviderConfig(
                        name=provider_name,
                        api_key=api_key,
                        models=[],  # Auto-detect
                    ))
        
        # Ollama from env
        if ollama_url := os.getenv("OLLAMA_BASE_URL"):
            existing = config.get_provider("ollama")
            if existing:
                existing.base_url = ollama_url
            else:
                config.providers.append(ProviderConfig(
                    name="ollama",
                    base_url=ollama_url,
                    models=["qwen2.5-coder:7b"],
                ))
        
        return config

    def save(self, path: Path | None = None) -> Path:
        """Persist current config to YAML."""
        path = path or DEFAULT_CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return path

    @staticmethod
    def write_template(path: Path | None = None) -> Path:
        """Write the default config template."""
        path = path or DEFAULT_CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG_TEMPLATE)
        return path

    @property
    def proxy_url(self) -> str:
        return f"http://{self.proxy.host}:{self.proxy.port}"

    def get_provider(self, name: str) -> ProviderConfig | None:
        for p in self.providers:
            if p.name == name:
                return p
        return None

    def provider_names(self) -> list[str]:
        return [p.name for p in self.providers]

    def auto_add_providers(self) -> None:
        """Auto-detect and add providers from environment variables."""
        # Standard API key environment variables
        api_keys = {
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        }
        base_urls = {
            "openai": os.getenv("OPENAI_BASE_URL"),
            "anthropic": os.getenv("ANTHROPIC_BASE_URL"),
            "ollama": os.getenv("OLLAMA_BASE_URL"),
        }

        for provider_name, api_key in api_keys.items():
            if api_key:
                existing = self.get_provider(provider_name)
                if existing:
                    existing.api_key = api_key
                    if base_urls.get(provider_name):
                        existing.base_url = base_urls[provider_name]
                else:
                    self.providers.append(ProviderConfig(
                        name=provider_name,
                        api_key=api_key,
                        base_url=base_urls.get(provider_name),
                        models=[],
                    ))

        # Ollama without API key
        if ollama_url := os.getenv("OLLAMA_BASE_URL"):
            existing = self.get_provider("ollama")
            if existing:
                existing.base_url = ollama_url
            else:
                self.providers.append(ProviderConfig(
                    name="ollama",
                    base_url=ollama_url,
                    models=["qwen2.5-coder:7b"],
                ))
