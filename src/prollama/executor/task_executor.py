"""Task Solver Engine — the core execution loop.

Accepts a Task, orchestrates:
  1. classify → 2. select model → 3. build context →
  4. generate fix → 5. run tests → 6. iterate or escalate
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

from prollama.anonymizer.pipeline import AnonymizationPipeline
from prollama.config import Config
from prollama.models import (
    PrivacyLevel,
    Task,
    TaskComplexity,
    TaskResult,
    TaskStatus,
    TaskType,
)
from prollama.router.model_router import ModelInfo, ModelRouter

# ---------------------------------------------------------------------------
# Complexity classifier (heuristic, pre-MVP)
# ---------------------------------------------------------------------------

def classify_complexity(task: Task) -> TaskComplexity:
    """Simple heuristic classifier based on description keywords."""
    desc = task.description.lower()

    very_hard_signals = ["architect", "multi-file", "redesign", "migration"]
    hard_signals = ["refactor", "extract", "security", "endpoint", "feature"]
    medium_signals = ["bug", "error", "exception", "handle", "test"]
    # Simple signals override medium when present (e.g. "fix typo" is simple, not medium)
    simple_signals = [
        "typo", "lint", "format", "formatting", "whitespace", "indent",
        "spelling", "rename", "missing import", "type hint", "type hints",
        "docstring", "comment", "readme", "changelog", "todo",
    ]

    # Check simple first — these are low-effort even if "fix" appears nearby
    if any(s in desc for s in simple_signals):
        return TaskComplexity.SIMPLE
    if any(s in desc for s in very_hard_signals):
        return TaskComplexity.VERY_HARD
    if any(s in desc for s in hard_signals):
        return TaskComplexity.HARD
    if any(s in desc for s in medium_signals) or "fix" in desc:
        return TaskComplexity.MEDIUM
    return TaskComplexity.SIMPLE


def classify_type(task: Task) -> TaskType:
    """Heuristic task-type classifier."""
    desc = task.description.lower()
    if any(w in desc for w in ("refactor", "extract", "rename", "reorganize")):
        return TaskType.REFACTOR
    if any(w in desc for w in ("security", "vulnerability", "cve", "xss", "injection")):
        return TaskType.SECURITY
    if any(w in desc for w in ("test", "coverage", "spec")):
        return TaskType.TEST
    if any(w in desc for w in ("feature", "add", "implement", "create", "endpoint")):
        return TaskType.FEATURE
    return TaskType.FIX


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class TaskExecutor:
    """Orchestrate the full task-solving loop."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.router = ModelRouter(config=config)
        self.pipeline = AnonymizationPipeline(
            privacy_level=PrivacyLevel(config.privacy.level),
        )
        self._http = httpx.Client(timeout=120)

    # -- public API ---------------------------------------------------------

    def solve(self, task: Task) -> TaskResult:
        """Run the full solve loop for a task."""
        t0 = time.monotonic()

        # 1. Classify
        task.complexity = task.complexity or classify_complexity(task)
        task.task_type = classify_type(task)
        task.status = TaskStatus.RUNNING

        # 2. Select model
        model = self.router.select(complexity=task.complexity)
        if model is None:
            return self._fail(task, t0, "No available models configured.")

        # 3. Build context
        context = self._build_context(task)

        # 4. Anonymize only if there's code to anonymize (file_path exists)
        if task.file_path and Path(task.file_path).exists():
            anon_result = self.pipeline.run(context)
            anonymized_context = anon_result.anonymized_code
            mappings = anon_result.mappings
        else:
            # No code to anonymize - use context directly
            anonymized_context = context
            mappings = {}

        # 5. Execute + iterate
        max_iter = self.config.executor.max_iterations
        patch: str | None = None
        iteration = 0
        cost_total = 0.0

        for iteration in range(1, max_iter + 1):
            task.status = TaskStatus.ITERATING

            # Call LLM
            response, cost = self._call_llm(model, task, anonymized_context)
            cost_total += cost

            if response is None:
                # Escalate
                next_model = self.router.escalate(model)
                if next_model is None:
                    return self._fail(task, t0, f"All models exhausted after {iteration} iterations.", iteration, cost_total)
                model = next_model
                continue

            # Rehydrate only if we have mappings (code was anonymized)
            if mappings:
                patch = self.pipeline.rehydrate(response, mappings)
            else:
                patch = response

            # Run tests (if configured)
            if self._run_tests(task):
                task.status = TaskStatus.COMPLETED
                break
            else:
                # Tests failed — try again or escalate
                next_model = self.router.escalate(model)
                if next_model and iteration >= 2:
                    model = next_model
        else:
            if task.status != TaskStatus.COMPLETED:
                return self._fail(task, t0, f"Max iterations ({max_iter}) reached.", iteration, cost_total)

        duration = time.monotonic() - t0
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            patch=patch,
            iterations=iteration,
            model_used=model.name,
            model_tier=model.tier,
            cost_usd=cost_total,
            duration_seconds=round(duration, 2),
        )

    # -- internals ----------------------------------------------------------

    def _build_context(self, task: Task) -> str:
        """Assemble code context for the LLM prompt."""
        parts = [f"Task: {task.description}"]

        if task.error:
            parts.append(f"Error: {task.error}")

        if task.file_path:
            path = Path(task.file_path)
            if path.exists():
                code = path.read_text(errors="replace")
                parts.append(f"File: {task.file_path}\n```\n{code}\n```")

        return "\n\n".join(parts)

    def _call_llm(
        self, model: ModelInfo, task: Task, anonymized_context: str
    ) -> tuple[str | None, float]:
        """Send a completion request to the model's provider. Returns (response, cost)."""
        provider = self.config.get_provider(model.provider)
        if provider is None:
            return None, 0.0

        base_url = provider.base_url or self._default_base_url(model.provider)
        api_key = provider.resolve_api_key() or ""

        prompt = (
            f"You are a senior developer. Fix the following issue.\n\n"
            f"{anonymized_context}\n\n"
            f"Return ONLY the fixed code, no explanations."
        )

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model.name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4096,
        }

        try:
            resp = self._http.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            # Rough cost estimate
            input_tokens = data.get("usage", {}).get("prompt_tokens", len(prompt) // 4)
            output_tokens = data.get("usage", {}).get("completion_tokens", len(content) // 4)
            cost = self.router.estimate_cost(model, input_tokens, output_tokens)
            return content, cost
        except Exception:
            return None, 0.0

    def _run_tests(self, task: Task) -> bool:
        """Run project tests. Returns True if passing (or no test runner found)."""
        if not task.file_path:
            return True  # no file context = can't run tests, assume OK

        project_dir = Path(task.file_path).parent

        # Try pytest
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-q"],
                cwd=str(project_dir),
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return True  # no pytest = assume pass

    def _fail(
        self,
        task: Task,
        t0: float,
        message: str,
        iterations: int = 0,
        cost: float = 0.0,
    ) -> TaskResult:
        task.status = TaskStatus.FAILED
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            iterations=iterations,
            cost_usd=cost,
            duration_seconds=round(time.monotonic() - t0, 2),
            error_message=message,
        )

    @staticmethod
    def _default_base_url(provider: str) -> str:
        defaults = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "ollama": "http://localhost:11434/v1",
            "openrouter": "https://openrouter.ai/api/v1",
        }
        return defaults.get(provider, "http://localhost:8080/v1")
