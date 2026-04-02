"""Shared test fixtures for prollama test suite."""

from pathlib import Path

import pytest

from prollama.config import Config, ProviderConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def config_ollama() -> Config:
    """Config with only Ollama provider."""
    return Config(providers=[
        ProviderConfig(name="ollama", base_url="http://localhost:11434/v1"),
    ])


@pytest.fixture
def config_multi() -> Config:
    """Config with multiple providers."""
    return Config(providers=[
        ProviderConfig(name="ollama", base_url="http://localhost:11434/v1"),
        ProviderConfig(name="openai", api_key="sk-test", models=["gpt-4o-mini", "gpt-4o"]),
        ProviderConfig(
            name="anthropic",
            api_key="sk-ant-test",
            models=["claude-sonnet-4-20250514"],
        ),
    ])


@pytest.fixture
def config_empty() -> Config:
    """Config with no providers."""
    return Config()


@pytest.fixture
def secrets_heavy_code() -> str:
    """Source code with many secrets and PII."""
    return (FIXTURES_DIR / "secrets_heavy.py").read_text()


@pytest.fixture
def clean_code() -> str:
    """Source code with no sensitive data."""
    return (FIXTURES_DIR / "clean_code.py").read_text()


@pytest.fixture
def fintech_code() -> str:
    """Fintech application source code."""
    examples_dir = Path(__file__).parent.parent / "examples" / "sample_code"
    return (examples_dir / "fintech_app.py").read_text()
