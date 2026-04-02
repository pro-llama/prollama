"""Tests for prollama configuration."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from prollama.config import Config, ProviderConfig


class TestConfigBasics:
    """Test basic configuration functionality."""

    def test_default_config(self):
        config = Config()
        assert config.version == "0.2.0"
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_config_with_values(self):
        config = Config(
            debug=True,
            log_level="DEBUG",
            proxy_url="http://custom.proxy:8080"
        )
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.proxy_url == "http://custom.proxy:8080"

    def test_provider_operations(self):
        config = Config()
        provider = ProviderConfig(
            name="openai",
            api_key="sk-test-key",
            base_url="https://api.openai.com/v1"
        )
        
        config.add_provider(provider)
        assert len(config.providers) == 1
        assert config.provider_names() == ["openai"]
        
        # Test getting provider
        retrieved = config.get_provider("openai")
        assert retrieved is not None
        assert retrieved.api_key == "sk-test-key"
        
        # Test removing provider
        config.remove_provider("openai")
        assert len(config.providers) == 0


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

    def test_load_nonexistent_defaults(self):
        config = Config.load(Path("/nonexistent/config.yaml"))
        assert config.version == "0.2.0"
        assert len(config.providers) == 0

    def test_load_from_file(self, tmp_path):
        config_data = {
            "version": "0.1.0",
            "debug": True,
            "providers": [
                {
                    "name": "openai",
                    "api_key": "sk-test-key",
                    "base_url": "https://api.openai.com/v1"
                }
            ]
        }
        
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        loaded = Config.load(config_path)
        assert loaded.version == "0.1.0"
        assert loaded.debug is True
        assert len(loaded.providers) == 1
        assert loaded.providers[0].name == "openai"

    def test_create_template(self, tmp_path):
        template_path = tmp_path / "template.yaml"
        Config.create_template(template_path)
        
        assert template_path.exists()
        with open(template_path) as f:
            content = f.read()
            assert "# Prollama Configuration Template" in content
            assert "version:" in content
            assert "providers:" in content


class TestProviderConfig:
    """Test provider configuration."""

    def test_provider_config_creation(self):
        provider = ProviderConfig(
            name="test",
            api_key="key123",
            base_url="https://api.test.com"
        )
        assert provider.name == "test"
        assert provider.api_key == "key123"
        assert provider.base_url == "https://api.test.com"
        assert provider.models == []

    def test_resolve_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "env-key-456")
        
        provider = ProviderConfig(
            name="test",
            api_key="${TEST_API_KEY}"
        )
        
        assert provider.resolve_api_key() == "env-key-456"

    def test_resolve_api_key_literal(self):
        provider = ProviderConfig(
            name="test",
            api_key="sk-literal-key"
        )
        
        assert provider.resolve_api_key() == "sk-literal-key"

    def test_proxy_url(self):
        config = Config()
        assert config.proxy_url == "http://127.0.0.1:8741"
