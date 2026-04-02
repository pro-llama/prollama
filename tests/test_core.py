"""Tests for prollama core functionality."""

import pytest
from unittest.mock import Mock, patch

from prollama.config import Config, ProviderConfig
from prollama.llm import LLMClient


class TestLLMClient:
    """Test LLM client functionality."""

    def test_client_creation_with_provider(self):
        """Test creating client with a provider config."""
        provider = ProviderConfig(
            name="test",
            api_key="sk-test-key",
            base_url="https://api.test.com/v1"
        )
        client = LLMClient(provider)
        assert client.provider.name == "test"
        assert client.provider.api_key == "sk-test-key"

    def test_client_with_env_api_key(self, monkeypatch):
        """Test client resolves API key from environment."""
        monkeypatch.setenv("TEST_API_KEY", "env-key-456")
        
        provider = ProviderConfig(
            name="test",
            api_key="${TEST_API_KEY}",
            base_url="https://api.test.com/v1"
        )
        client = LLMClient(provider)
        assert client.resolve_api_key() == "env-key-456"

    @patch('requests.post')
    def test_simple_completion(self, mock_post):
        """Test simple text completion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, world!"}}]
        }
        mock_post.return_value = mock_response
        
        provider = ProviderConfig(
            name="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1"
        )
        client = LLMClient(provider)
        
        result = client.complete("Say hello")
        assert result == "Hello, world!"
        mock_post.assert_called_once()

    def test_client_validation(self):
        """Test client validates required fields."""
        with pytest.raises(ValueError, match="API key is required"):
            provider = ProviderConfig(name="test", api_key="")
            LLMClient(provider)

    def test_model_listing(self):
        """Test listing available models."""
        provider = ProviderConfig(
            name="test",
            api_key="sk-test",
            models=["gpt-4", "gpt-3.5-turbo"]
        )
        client = LLMClient(provider)
        models = client.list_models()
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
