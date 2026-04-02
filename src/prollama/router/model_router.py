"""Model routing engine — selects the cheapest model that can handle the task.

Implements the escalation strategy:
  cheap model → mid-tier → premium → top
If a cheap model fails after N attempts, the router escalates to the next tier.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from prollama.config import Config
from prollama.models import ModelTier, TaskComplexity

# ---------------------------------------------------------------------------
# Model catalog (default cost estimates per 1M input tokens)
# ---------------------------------------------------------------------------

@dataclass
class ModelInfo:
    name: str
    provider: str
    tier: ModelTier
    cost_per_1m_input: float  # USD
    cost_per_1m_output: float  # USD
    context_window: int = 32_000
    local: bool = False


DEFAULT_MODELS: list[ModelInfo] = [
    # Local / cheap
    ModelInfo("qwen2.5-coder:7b",  "ollama",    ModelTier.CHEAP,   0.0,   0.0,  32_000, local=True),
    ModelInfo("qwen2.5-coder:32b", "ollama",    ModelTier.MID,     0.0,   0.0,  32_000, local=True),
    ModelInfo("deepseek-coder-v2:16b", "ollama", ModelTier.MID,    0.0,   0.0,  32_000, local=True),

    # Cloud — cheap
    ModelInfo("openai/gpt-5.4-mini",      "openrouter", ModelTier.CHEAP,   0.10,  0.30,  128_000),
    ModelInfo("x-ai/grok-code-fast-1",      "openrouter", ModelTier.CHEAP,   0.50,  1.00,  128_000),
    ModelInfo("qwen/qwen3-coder-next",      "openrouter", ModelTier.CHEAP,   0.20,  0.60,  131_000),
    ModelInfo("deepseek/deepseek-coder-v3",  "openrouter", ModelTier.MID,     0.50,  1.50,  128_000),

    # Cloud — premium
    ModelInfo("gpt-4o-mini",       "openai",    ModelTier.PREMIUM,  0.15,   0.60, 128_000),
    ModelInfo("claude-haiku-4-5-20251001",   "anthropic", ModelTier.PREMIUM, 0.80, 4.00, 200_000),

    # Cloud — top
    ModelInfo("gpt-4o",            "openai",    ModelTier.TOP,      2.50,  10.00, 128_000),
    ModelInfo("claude-sonnet-4-20250514",    "anthropic", ModelTier.TOP,    3.00, 15.00, 200_000),
]


# ---------------------------------------------------------------------------
# Tier ordering for escalation
# ---------------------------------------------------------------------------

TIER_ORDER = [ModelTier.CHEAP, ModelTier.MID, ModelTier.PREMIUM, ModelTier.TOP]


def _complexity_to_start_tier(complexity: TaskComplexity | None) -> ModelTier:
    """Determine starting tier based on task complexity."""
    mapping = {
        TaskComplexity.SIMPLE: ModelTier.CHEAP,
        TaskComplexity.MEDIUM: ModelTier.MID,
        TaskComplexity.HARD: ModelTier.PREMIUM,
        TaskComplexity.VERY_HARD: ModelTier.TOP,
    }
    return mapping.get(complexity, ModelTier.CHEAP)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

@dataclass
class ModelRouter:
    """Select and escalate models based on task complexity and strategy."""

    config: Config
    catalog: list[ModelInfo] = field(default_factory=lambda: list(DEFAULT_MODELS))

    def available_models(self) -> list[ModelInfo]:
        """Filter catalog to only models whose provider is configured."""
        provider_names = {p.name for p in self.config.providers}
        # Also include ollama-based models if ollama provider is configured
        return [m for m in self.catalog if m.provider in provider_names]

    def select(
        self,
        complexity: TaskComplexity | None = None,
        preferred_tier: ModelTier | None = None,
    ) -> ModelInfo | None:
        """Pick the best model for a given task complexity."""
        available = self.available_models()
        if not available:
            return None

        # Check for preferred model from LLM_MODEL env var
        if self.config.executor.llm_model:
            preferred_name = self.config.executor.llm_model
            # Strip openrouter/ prefix if present for matching
            if preferred_name.startswith("openrouter/"):
                preferred_name = preferred_name[11:]
            for m in available:
                if m.name == preferred_name or m.name.endswith(preferred_name):
                    return m

        strategy = self.config.routing.strategy
        start_tier = preferred_tier or _complexity_to_start_tier(complexity)

        if strategy == "local-first":
            local = [m for m in available if m.local]
            if local:
                return min(local, key=lambda m: TIER_ORDER.index(m.tier))

        # Cost-optimized: find cheapest model at or above the required tier
        start_idx = TIER_ORDER.index(start_tier)
        for tier in TIER_ORDER[start_idx:]:
            candidates = [m for m in available if m.tier == tier]
            if candidates:
                return min(candidates, key=lambda m: m.cost_per_1m_input)

        # Fallback: any available model
        if self.config.routing.fallback and available:
            return min(available, key=lambda m: m.cost_per_1m_input)

        return None

    def escalate(self, current_model: ModelInfo) -> ModelInfo | None:
        """Get the next-tier model after a failure."""
        # Check for fallback model from LLM_FALLBACK_MODEL env var
        if self.config.executor.llm_fallback_model:
            fallback_name = self.config.executor.llm_fallback_model
            # Strip openrouter/ prefix if present for matching
            if fallback_name.startswith("openrouter/"):
                fallback_name = fallback_name[11:]
            available = self.available_models()
            for m in available:
                if m.name == fallback_name or m.name.endswith(fallback_name):
                    return m

        current_idx = TIER_ORDER.index(current_model.tier)
        if current_idx >= len(TIER_ORDER) - 1:
            return None  # already at top tier

        next_tier = TIER_ORDER[current_idx + 1]
        return self.select(preferred_tier=next_tier)

    def estimate_cost(self, model: ModelInfo, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a single call in USD."""
        input_cost = (input_tokens / 1_000_000) * model.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * model.cost_per_1m_output
        return input_cost + output_cost
