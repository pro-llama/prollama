"""Tests for configuration loading, saving, and management."""


import yaml

from prollama.config import DEFAULT_CONFIG_TEMPLATE, Config, ProviderConfig


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_proxy_port(self):
        config = Config()
        assert config.proxy.port == 8741

    def test_default_privacy_level(self):
        config = Config()
        assert config.privacy.level == "full"

    def test_default_routing_strategy(self):
        config = Config()
        assert config.routing.strategy == "cost-optimized"

    def test_default_executor_settings(self):
        config = Config()
        assert config.executor.max_iterations == 5
        assert config.executor.budget == 5.00
        assert config.executor.strategy == "auto"

    def test_default_no_providers(self):
        config = Config()
        assert config.providers == []


class TestConfigProviders:
    """Test provider configuration."""

    def test_provider_names(self):
        config = Config(providers=[
            ProviderConfig(name="ollama"),
            ProviderConfig(name="openai"),
        ])
        assert config.provider_names() == ["ollama", "openai"]

    def test_get_provider_existing(self):
        config = Config(providers=[ProviderConfig(name="ollama")])
        assert config.get_provider("ollama") is not None

    def test_get_provider_missing(self):
        config = Config(providers=[ProviderConfig(name="ollama")])
        assert config.get_provider("openai") is None

    def test_resolve_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("MY_API_KEY", "secret-123")
        provider = ProviderConfig(name="test", api_key="${MY_API_KEY}")
        assert provider.resolve_api_key() == "secret-123"

    def test_resolve_api_key_missing_env(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_KEY", raising=False)
        provider = ProviderConfig(name="test", api_key="${NONEXISTENT_KEY}")
        assert provider.resolve_api_key() is None

    def test_resolve_api_key_literal(self):
        provider = ProviderConfig(name="test", api_key="sk-literal-key")
        assert provider.resolve_api_key() == "sk-literal-key"

    def test_proxy_url(self):
        config = Config()
        assert config.proxy_url == "http://127.0.0.1:8741"


class TestConfigIO:
    """Test config save/load/template operations."""

    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        config = Config(providers=[
            ProviderConfig(name="ollama", base_url="http://localhost:11434/v1"),
        ])
        path = tmp_path / "config.yaml"
        config.save(path)
        assert path.exists()

        loaded = Config.load(path)
        assert loaded.provider_names() == ["ollama"]
        assert loaded.providers[0].base_url == "http://localhost:11434/v1"

    def test_load_nonexistent_returns_defaults(self, tmp_path):
        config = Config.load(tmp_path / "nonexistent.yaml")
        assert config.proxy.port == 8741

    def test_write_template(self, tmp_path):
        path = tmp_path / "config.yaml"
        Config.write_template(path)
        assert path.exists()
        content = path.read_text()
        assert "providers:" in content
        assert "privacy:" in content
        assert "routing:" in content

    def test_template_is_valid_yaml(self):
        parsed = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
        assert "providers" in parsed
        assert "privacy" in parsed

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "deep" / "config.yaml"
        config = Config()
        config.save(path)
        assert path.exists()
