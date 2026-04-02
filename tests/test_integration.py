"""Integration tests for prollama."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from prollama.config import Config, ProviderConfig, ProxyConfig
from prollama.proxy import Proxy
from prollama.llm import LLMClient


class TestIntegration:
    """Integration tests for the complete system."""

    def test_config_to_client_workflow(self, monkeypatch):
        """Test loading config and creating client."""
        # Clear environment variables that might auto-add providers
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
providers:
  - name: test-provider
    api_key: sk-test-key
    base_url: https://api.test.com/v1
    models:
      - gpt-4
      - gpt-3.5-turbo
"""
            f.write(config_content)
            f.flush()
            
            try:
                config = Config.load(Path(f.name))
                assert len(config.providers) == 1
                
                provider = config.providers[0]
                client = LLMClient(provider)
                assert client.provider.name == "test-provider"
                assert "gpt-4" in client.list_models()
            finally:
                os.unlink(f.name)

    @patch('requests.post')
    def test_end_to_end_completion(self, mock_post):
        """Test complete flow from config to LLM completion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        config = Config(providers=[
            ProviderConfig(
                name="openai",
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1"
            )
        ])
        
        client = LLMClient(config.providers[0])
        result = client.complete("Test prompt")
        
        assert result == "Test response"
        mock_post.assert_called_once()

    def test_proxy_integration(self):
        """Test proxy integration with config."""
        config = Config(
            proxy=ProxyConfig(host="localhost", port=8741),
            providers=[
                ProviderConfig(
                    name="test",
                    api_key="sk-test",
                    base_url="https://api.test.com"
                )
            ]
        )
        
        proxy = Proxy(config)
        assert proxy.config.proxy_url == "http://localhost:8741"
        assert len(proxy.config.providers) == 1

    def test_environment_variable_integration(self, monkeypatch):
        """Test integration with environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.openai.com")
        
        # Config should auto-detect environment variables
        config = Config()
        config.auto_add_providers()
        
        openai_provider = config.get_provider("openai")
        if openai_provider:
            assert openai_provider.resolve_api_key() == "sk-env-key"
            assert openai_provider.base_url == "https://custom.openai.com"

    def test_config_save_load_cycle(self, tmp_path, monkeypatch):
        """Test complete config save/load cycle."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("PROXY_HOST", raising=False)
        monkeypatch.delenv("PROXY_PORT", raising=False)
        
        # Create original config
        original = Config(
            debug=True,
            proxy=ProxyConfig(host="test.proxy", port=8080),
            providers=[
                ProviderConfig(
                    name="provider1",
                    api_key="sk-key1",
                    base_url="https://api1.com"
                ),
                ProviderConfig(
                    name="provider2",
                    api_key="${TEST_KEY}",
                    base_url="https://api2.com"
                )
            ]
        )
        
        # Save config
        config_path = tmp_path / "test_config.yaml"
        original.save(config_path)
        
        # Load config
        loaded = Config.load(config_path)
        
        # Verify loaded config matches original
        assert loaded.debug is True
        assert loaded.proxy_url == "http://test.proxy:8080"
        assert len(loaded.providers) == 2
        
        provider1 = loaded.get_provider("provider1")
        assert provider1.api_key == "sk-key1"
        
        provider2 = loaded.get_provider("provider2")
        assert provider2.api_key == "${TEST_KEY}"

    def test_error_propagation(self):
        """Test that errors are properly propagated through the system."""
        config = Config(providers=[
            ProviderConfig(
                name="invalid",
                api_key="",  # Invalid empty key
                base_url="https://api.test.com"
            )
        ])
        
        # Should raise error when trying to create client
        with pytest.raises(ValueError, match="API key is required"):
            LLMClient(config.providers[0])

    def test_multiple_providers_isolation(self):
        """Test that multiple providers don't interfere with each other."""
        config = Config(providers=[
            ProviderConfig(
                name="provider1",
                api_key="sk-key1",
                base_url="https://api1.com",
                models=["model1", "model2"]
            ),
            ProviderConfig(
                name="provider2",
                api_key="sk-key2",
                base_url="https://api2.com",
                models=["model3", "model4"]
            )
        ])
        
        client1 = LLMClient(config.providers[0])
        client2 = LLMClient(config.providers[1])
        
        assert client1.resolve_api_key() == "sk-key1"
        assert client2.resolve_api_key() == "sk-key2"
        
        models1 = client1.list_models()
        models2 = client2.list_models()
        
        assert "model1" in models1
        assert "model3" in models2
        assert "model3" not in models1
        assert "model1" not in models2
