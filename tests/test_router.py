"""Tests for model routing and cost estimation."""

from prollama.config import Config, ProviderConfig, RoutingConfig
from prollama.models import ModelTier, TaskComplexity
from prollama.router.model_router import ModelRouter


class TestModelSelection:
    """Test model selection for different complexity levels."""

    def test_simple_selects_cheap(self, config_ollama):
        router = ModelRouter(config=config_ollama)
        model = router.select(complexity=TaskComplexity.SIMPLE)
        assert model is not None
        assert model.tier == ModelTier.CHEAP

    def test_medium_selects_mid(self, config_ollama):
        router = ModelRouter(config=config_ollama)
        model = router.select(complexity=TaskComplexity.MEDIUM)
        assert model is not None
        assert model.tier == ModelTier.MID

    def test_hard_with_cloud_selects_premium(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(complexity=TaskComplexity.HARD)
        assert model is not None
        assert model.tier == ModelTier.PREMIUM

    def test_very_hard_selects_top(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(complexity=TaskComplexity.VERY_HARD)
        assert model is not None
        assert model.tier == ModelTier.TOP

    def test_no_providers_returns_none(self, config_empty):
        router = ModelRouter(config=config_empty)
        assert router.select() is None

    def test_preferred_tier_override(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(preferred_tier=ModelTier.TOP)
        assert model is not None
        assert model.tier == ModelTier.TOP


class TestEscalation:
    """Test model escalation chain."""

    def test_cheap_escalates_to_mid(self, config_ollama):
        router = ModelRouter(config=config_ollama)
        cheap = router.select(preferred_tier=ModelTier.CHEAP)
        mid = router.escalate(cheap)
        assert mid is not None
        assert mid.tier == ModelTier.MID

    def test_top_cannot_escalate(self, config_multi):
        router = ModelRouter(config=config_multi)
        top = router.select(preferred_tier=ModelTier.TOP)
        assert router.escalate(top) is None

    def test_full_escalation_chain(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(preferred_tier=ModelTier.CHEAP)
        tiers = [model.tier]
        while model:
            model = router.escalate(model)
            if model:
                tiers.append(model.tier)
        # Should have at least cheap → mid → premium → top
        assert len(tiers) >= 3
        # Tiers should be ascending
        tier_order = [ModelTier.CHEAP, ModelTier.MID, ModelTier.PREMIUM, ModelTier.TOP]
        for i in range(len(tiers) - 1):
            assert tier_order.index(tiers[i]) < tier_order.index(tiers[i + 1])


class TestRoutingStrategy:
    """Test different routing strategies."""

    def test_local_first_prefers_local(self):
        config = Config(
            providers=[
                ProviderConfig(name="ollama", base_url="http://localhost:11434/v1"),
                ProviderConfig(name="openai", api_key="sk-test", models=["gpt-4o"]),
            ],
            routing=RoutingConfig(strategy="local-first"),
        )
        router = ModelRouter(config=config)
        model = router.select(complexity=TaskComplexity.HARD)
        assert model is not None
        assert model.local is True

    def test_cost_optimized_picks_cheapest(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(complexity=TaskComplexity.SIMPLE)
        assert model is not None
        # Should be a local free model
        assert model.cost_per_1m_input == 0.0


class TestCostEstimation:
    """Test cost calculation."""

    def test_local_model_free(self, config_ollama):
        router = ModelRouter(config=config_ollama)
        model = router.select()
        cost = router.estimate_cost(model, input_tokens=10000, output_tokens=5000)
        assert cost == 0.0

    def test_cloud_model_costs(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(preferred_tier=ModelTier.TOP)
        cost = router.estimate_cost(model, input_tokens=1000, output_tokens=500)
        assert cost > 0.0

    def test_cost_proportional_to_tokens(self, config_multi):
        router = ModelRouter(config=config_multi)
        model = router.select(preferred_tier=ModelTier.TOP)
        cost_small = router.estimate_cost(model, 100, 50)
        cost_large = router.estimate_cost(model, 10000, 5000)
        assert cost_large > cost_small * 50  # Roughly proportional


class TestAvailableModels:
    """Test model filtering by configured providers."""

    def test_only_ollama_models_with_ollama_config(self, config_ollama):
        router = ModelRouter(config=config_ollama)
        models = router.available_models()
        assert all(m.provider == "ollama" for m in models)

    def test_multi_provider_models(self, config_multi):
        router = ModelRouter(config=config_multi)
        models = router.available_models()
        providers = {m.provider for m in models}
        assert "ollama" in providers
        assert "openai" in providers

    def test_no_providers_no_models(self, config_empty):
        router = ModelRouter(config=config_empty)
        assert router.available_models() == []
