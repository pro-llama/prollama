# Model Routing

prollama's model router selects the cheapest model capable of handling each task,
and escalates to more expensive models only when cheaper ones fail.

## How It Works

```
Task received
    │
    ▼
Classify complexity: SIMPLE → MEDIUM → HARD → VERY_HARD
    │
    ▼
Map to starting tier: CHEAP → MID → PREMIUM → TOP
    │
    ▼
Select cheapest available model at that tier
    │
    ▼
Execute task
    │
    ├─ Success → Done (paid minimum cost)
    │
    └─ Failure → Escalate to next tier → Retry
```

## Model Tiers

| Tier | Examples | Cost (per 1M tokens) | Use Case |
|------|----------|---------------------|----------|
| CHEAP | qwen2.5-coder:7b (local), Qwen3-Coder | $0 – $0.20 | Lint, typos, type hints, simple fixes |
| MID | qwen2.5-coder:32b (local), DeepSeek-Coder-V3 | $0 – $1.50 | Bug fixes, error handling, small features |
| PREMIUM | GPT-4o-mini, Claude Haiku | $0.15 – $4.00 | Refactors, new endpoints, test generation |
| TOP | GPT-4o, Claude Sonnet | $2.50 – $15.00 | Architecture, multi-file, security fixes |

## Routing Strategies

### cost-optimized (default)

Starts at the tier matching task complexity, picks the cheapest model.
Escalates only on failure. Minimizes cost — approximately 60-80% cheaper
than always using premium models.

### quality-first

Always uses the highest-tier model available. More expensive but
faster for complex tasks (no failed attempts on cheaper models).

### local-first

Prefers local models (Ollama) regardless of tier. Falls back to cloud
only when no local model is available. Guarantees zero data leaves
your network.

## Complexity Classification

prollama classifies task complexity using keyword heuristics:

| Complexity | Keywords | Starting Tier |
|-----------|----------|---------------|
| SIMPLE | typo, lint, format, type hint, docstring, readme | CHEAP |
| MEDIUM | bug, fix, error, exception, handle, test | MID |
| HARD | refactor, extract, security, endpoint, feature | PREMIUM |
| VERY_HARD | architect, multi-file, redesign, migration | TOP |

## Cost Estimation

```python
from prollama.router import ModelRouter
from prollama.config import Config

router = ModelRouter(config=Config.load())
model = router.select(complexity=TaskComplexity.SIMPLE)

# Estimate cost before execution
cost = router.estimate_cost(model, input_tokens=2000, output_tokens=500)
print(f"Estimated cost: ${cost:.4f}")
```

## Adding Custom Models

Add models to the router catalog programmatically:

```python
from prollama.router.model_router import ModelInfo, ModelTier

router.catalog.append(ModelInfo(
    name="my-finetuned-coder",
    provider="ollama",
    tier=ModelTier.MID,
    cost_per_1m_input=0.0,
    cost_per_1m_output=0.0,
    context_window=32_000,
    local=True,
))
```
