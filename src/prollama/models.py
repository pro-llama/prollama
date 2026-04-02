"""Domain models shared across prollama subsystems."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class TaskType(str, Enum):
    FIX = "fix"
    REFACTOR = "refactor"
    FEATURE = "feature"
    SECURITY = "security"
    TEST = "test"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"


class PrivacyLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"     # regex only
    FULL = "full"       # regex + NLP + AST


class ModelTier(str, Enum):
    CHEAP = "cheap"         # Qwen-Coder-8B, local Ollama
    MID = "mid"             # Qwen-Coder-32B, DeepSeek-Coder-V3
    PREMIUM = "premium"     # Claude Haiku, GPT-4o-mini
    TOP = "top"             # Claude Sonnet, GPT-4o


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class AnonymizationMapping(BaseModel):
    """Tracks original ↔ anonymized token pairs for rehydration."""
    original: str
    replacement: str
    category: str  # SECRET, EMAIL, PII, AST_IDENT, ...
    position: tuple[int, int] | None = None  # (line, col) if known


class AnonymizationResult(BaseModel):
    """Output of the anonymization pipeline."""
    anonymized_code: str
    mappings: list[AnonymizationMapping] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)  # {category: count}
    privacy_level: PrivacyLevel = PrivacyLevel.BASIC


class Task(BaseModel):
    """A unit of work submitted to the executor."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str
    file_path: str | None = None
    error: str | None = None
    ticket_ref: str | None = None  # e.g. "github:org/repo#142"
    task_type: TaskType = TaskType.FIX
    complexity: TaskComplexity | None = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Result of a completed (or failed) task."""
    task_id: str
    status: TaskStatus
    patch: str | None = None
    iterations: int = 0
    model_used: str | None = None
    model_tier: ModelTier | None = None
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    error_message: str | None = None
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProxyRequest(BaseModel):
    """Incoming chat completion request (OpenAI-compatible subset)."""
    model: str
    messages: list[dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
