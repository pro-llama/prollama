# API Reference

prollama can be used as a Python library for programmatic access to all functionality.

## Anonymization

### AnonymizationPipeline

```python
from prollama.anonymizer import AnonymizationPipeline
from prollama.models import PrivacyLevel

# Create pipeline
pipeline = AnonymizationPipeline(PrivacyLevel.FULL)

# Anonymize code
result = pipeline.run(source_code, language="python")

result.anonymized_code   # str — anonymized source
result.mappings          # list[AnonymizationMapping] — for rehydration
result.stats             # dict[str, int] — {"SECRET": 3, "AST_IDENT": 15}
result.privacy_level     # PrivacyLevel.FULL

# Rehydrate (restore originals)
original = pipeline.rehydrate(llm_response, result.mappings)
```

### RegexAnonymizer

```python
from prollama.anonymizer import RegexAnonymizer

anon = RegexAnonymizer()
anonymized_code, mappings = anon.anonymize(source_code)
restored = anon.rehydrate(anonymized_code, mappings)
```

### ASTAnonymizer

```python
from prollama.anonymizer.ast_layer import ASTAnonymizer

ast_anon = ASTAnonymizer(language="python")
anonymized, mappings = ast_anon.anonymize(source_code)
restored = ast_anon.rehydrate(anonymized, mappings)
```

## Model Routing

### ModelRouter

```python
from prollama.config import Config
from prollama.router import ModelRouter
from prollama.models import TaskComplexity, ModelTier

config = Config.load()
router = ModelRouter(config=config)

# List available models
models = router.available_models()

# Select model for task complexity
model = router.select(complexity=TaskComplexity.SIMPLE)   # cheapest
model = router.select(complexity=TaskComplexity.HARD)     # premium

# Escalate after failure
next_model = router.escalate(current_model)

# Estimate cost
cost = router.estimate_cost(model, input_tokens=1000, output_tokens=500)
```

## Task Execution

### TaskExecutor

```python
from prollama.config import Config
from prollama.executor import TaskExecutor
from prollama.models import Task

config = Config.load()
executor = TaskExecutor(config)

# Create a task
task = Task(
    description="Fix TypeError in payment.py line 87",
    file_path="src/payment.py",
    error="TypeError: 'NoneType' object has no attribute 'id'",
)

# Solve it
result = executor.solve(task)

result.status           # TaskStatus.COMPLETED or TaskStatus.FAILED
result.patch            # str — the generated fix
result.iterations       # int — number of attempts
result.model_used       # str — which model solved it
result.cost_usd         # float — total cost
result.duration_seconds # float — wall time
```

## Configuration

### Config

```python
from prollama.config import Config

# Load from default location
config = Config.load()

# Load from custom path
config = Config.load(Path("./my-config.yaml"))

# Create default
config = Config()

# Access settings
config.privacy.level          # "full"
config.routing.strategy       # "cost-optimized"
config.proxy.port             # 8741
config.provider_names()       # ["ollama", "openai"]
config.get_provider("ollama") # ProviderConfig | None

# Save
config.save()
config.save(Path("./custom.yaml"))
```

## Models

### Task

```python
from prollama.models import Task, TaskComplexity, TaskType

task = Task(
    description="Fix the bug",
    file_path="src/app.py",
    error="TypeError on line 42",
    ticket_ref="github:org/repo#142",
    task_type=TaskType.FIX,
    complexity=TaskComplexity.MEDIUM,
)
```

### TaskResult

```python
from prollama.models import TaskResult, TaskStatus

# Returned by TaskExecutor.solve()
result: TaskResult
result.task_id          # str
result.status           # TaskStatus.COMPLETED | FAILED
result.patch            # str | None
result.iterations       # int
result.model_used       # str | None
result.model_tier       # ModelTier | None
result.cost_usd         # float
result.duration_seconds # float
result.error_message    # str | None
```

### Enums

```python
from prollama.models import (
    TaskComplexity,  # SIMPLE, MEDIUM, HARD, VERY_HARD
    TaskType,        # FIX, REFACTOR, FEATURE, SECURITY, TEST
    TaskStatus,      # PENDING, QUEUED, RUNNING, ITERATING, COMPLETED, FAILED
    PrivacyLevel,    # NONE, BASIC, FULL
    ModelTier,       # CHEAP, MID, PREMIUM, TOP
)
```
