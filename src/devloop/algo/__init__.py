"""Progressive Algorithmization Loop.

The 5-stage pipeline: LLM → patterns → rules → hybrid → deterministic.

Usage:
    from devloop.algo.loop import Loop

    loop = Loop("./my-app")
    loop.discover()        # Stage 1: LLM handles all, collect traces
    loop.extract()         # Stage 2: identify hot paths
    loop.generate_rules()  # Stage 3: AI writes deterministic replacements
    loop.route()           # Stage 4: confidence-based routing
    loop.optimize()        # Stage 5: monitor, minimize LLM usage
    loop.report()          # show progress: % deterministic vs LLM
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class TraceEntry:
    """Single LLM interaction trace."""
    timestamp: float
    prompt_hash: str
    prompt_preview: str
    response_preview: str
    model: str = ""
    tier: str = ""
    cost_usd: float = 0.0
    elapsed_ms: float = 0.0
    pattern_id: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "prompt_hash": self.prompt_hash,
            "prompt_preview": self.prompt_preview[:200],
            "response_preview": self.response_preview[:200],
            "model": self.model,
            "tier": self.tier,
            "cost_usd": self.cost_usd,
            "elapsed_ms": self.elapsed_ms,
            "pattern_id": self.pattern_id,
            "confidence": self.confidence,
        }


@dataclass
class Pattern:
    """Extracted repeating pattern from traces."""
    id: str
    description: str
    frequency: int = 0
    avg_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    example_prompts: list[str] = field(default_factory=list)
    rule_generated: bool = False
    rule_code: str = ""
    confidence_threshold: float = 0.85


@dataclass
class Rule:
    """Deterministic replacement for an LLM pattern."""
    pattern_id: str
    name: str
    type: str = "regex"  # regex | lookup | decision_tree | function
    definition: str = ""
    pass_rate: float = 0.0
    cost_saved_usd: float = 0.0
    active: bool = False


@dataclass
class LoopState:
    """Current state of the progressive algorithmization loop."""
    stage: int = 0  # 0=init, 1=discover, 2=extract, 3=rules, 4=route, 5=optimize
    traces: list[TraceEntry] = field(default_factory=list)
    patterns: list[Pattern] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    total_requests: int = 0
    deterministic_requests: int = 0
    llm_requests: int = 0
    total_cost_usd: float = 0.0
    saved_cost_usd: float = 0.0

    @property
    def deterministic_ratio(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.deterministic_requests / self.total_requests

    @property
    def stage_name(self) -> str:
        names = {
            0: "init",
            1: "discovery",
            2: "pattern_extraction",
            3: "rule_generation",
            4: "hybrid_routing",
            5: "optimization",
        }
        return names.get(self.stage, "unknown")


class Loop:
    """The progressive algorithmization engine."""

    def __init__(self, project_path: str = "."):
        self.path = Path(project_path).resolve()
        self._store = self.path / ".devloop" / "algo"
        self._state = LoopState()
        self._load()

    # ── Stage 1: Discovery ────────────────────────────────

    def discover(self, proxy_url: str = "http://localhost:4000") -> LoopState:
        """Stage 1: Enable trace collection from proxym.

        Registers a webhook with proxym to capture all LLM interactions.
        Traces are stored locally for pattern analysis.
        """
        self._state.stage = max(self._state.stage, 1)

        # Try to register trace hook with proxym
        try:
            import httpx
            resp = httpx.post(
                f"{proxy_url}/v1/hooks/register",
                json={
                    "name": "devloop-trace",
                    "events": ["completion"],
                    "callback": "local",  # store in proxym, we poll
                },
                timeout=10,
            )
        except Exception:
            pass  # Works offline too — traces added manually via add_trace()

        self._save()
        return self._state

    def add_trace(self, prompt: str, response: str, **meta) -> TraceEntry:
        """Manually add a trace entry (or called by proxym hook)."""
        import hashlib
        entry = TraceEntry(
            timestamp=time.time(),
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:16],
            prompt_preview=prompt[:200],
            response_preview=response[:200],
            model=meta.get("model", ""),
            tier=meta.get("tier", ""),
            cost_usd=meta.get("cost_usd", 0.0),
            elapsed_ms=meta.get("elapsed_ms", 0.0),
        )
        self._state.traces.append(entry)
        self._state.total_requests += 1
        self._state.llm_requests += 1
        self._state.total_cost_usd += entry.cost_usd
        self._save()
        return entry

    # ── Stage 2: Pattern Extraction ───────────────────────

    def extract(self, min_frequency: int = 3) -> list[Pattern]:
        """Stage 2: Identify repeating patterns from traces.

        Groups traces by prompt similarity, ranks by frequency and cost.
        """
        self._state.stage = max(self._state.stage, 2)

        # Group by prompt hash (exact matches)
        hash_groups: dict[str, list[TraceEntry]] = {}
        for trace in self._state.traces:
            hash_groups.setdefault(trace.prompt_hash, []).append(trace)

        patterns = []
        for hash_val, traces in hash_groups.items():
            if len(traces) >= min_frequency:
                avg_cost = sum(t.cost_usd for t in traces) / len(traces)
                avg_lat = sum(t.elapsed_ms for t in traces) / len(traces)
                pattern = Pattern(
                    id=f"PAT-{hash_val[:8]}",
                    description=traces[0].prompt_preview[:100],
                    frequency=len(traces),
                    avg_cost_usd=avg_cost,
                    avg_latency_ms=avg_lat,
                    example_prompts=[t.prompt_preview for t in traces[:5]],
                )
                patterns.append(pattern)

        # Sort by potential savings (frequency * cost)
        patterns.sort(key=lambda p: p.frequency * p.avg_cost_usd, reverse=True)
        self._state.patterns = patterns
        self._save()
        return patterns

    # ── Stage 3: Rule Generation ──────────────────────────

    def generate_rules(self, use_llm: bool = True) -> list[Rule]:
        """Stage 3: Generate deterministic rules for top patterns.

        Uses LLM (via proxym) to create its own replacement:
        decision trees, lookup tables, regex matchers.
        """
        self._state.stage = max(self._state.stage, 3)

        rules = []
        for pattern in self._state.patterns[:10]:  # Top 10 patterns
            if pattern.rule_generated:
                continue

            rule = Rule(
                pattern_id=pattern.id,
                name=f"rule_{pattern.id.lower()}",
                type="lookup",
            )

            if use_llm:
                rule = self._llm_generate_rule(pattern, rule)

            pattern.rule_generated = True
            rules.append(rule)

        self._state.rules.extend(rules)
        self._save()
        return rules

    def _llm_generate_rule(self, pattern: Pattern, rule: Rule) -> Rule:
        """Ask LLM to generate a deterministic replacement for a pattern."""
        from devloop.tools.proxy import Proxy

        prompt = (
            f"I have a recurring LLM request pattern that appears {pattern.frequency} times.\n"
            f"Pattern: {pattern.description}\n"
            f"Examples:\n"
            + "\n".join(f"  - {ex}" for ex in pattern.example_prompts[:3])
            + "\n\n"
            "Generate a deterministic Python function that handles this pattern "
            "without needing an LLM. Return ONLY the function code."
        )

        try:
            with Proxy() as proxy:
                resp = proxy.ask(prompt, tier="standard")
                rule.definition = resp.content
                rule.type = "function"
                rule.active = True
        except Exception:
            rule.definition = f"# Auto-generation failed for {pattern.id}"

        return rule

    # ── Stage 4: Hybrid Routing ───────────────────────────

    def route(self, prompt: str) -> dict:
        """Stage 4: Route request to rule or LLM based on confidence.

        Returns:
            {"handler": "rule"|"llm", "rule_id": ..., "confidence": ...}
        """
        self._state.stage = max(self._state.stage, 4)

        # Check against active rules
        import hashlib
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        for rule in self._state.rules:
            if not rule.active:
                continue
            pattern = next(
                (p for p in self._state.patterns if p.id == rule.pattern_id), None
            )
            if not pattern:
                continue

            # Simple exact-match routing (extend with fuzzy later)
            if prompt_hash in [t.prompt_hash for t in self._state.traces
                               if t.pattern_id == pattern.id]:
                self._state.deterministic_requests += 1
                self._state.total_requests += 1
                self._state.saved_cost_usd += pattern.avg_cost_usd
                self._save()
                return {
                    "handler": "rule",
                    "rule_id": rule.pattern_id,
                    "confidence": pattern.confidence_threshold,
                    "cost_saved": pattern.avg_cost_usd,
                }

        # Fallback to LLM
        self._state.llm_requests += 1
        self._state.total_requests += 1
        self._save()
        return {"handler": "llm", "rule_id": None, "confidence": 0.0}

    # ── Stage 5: Optimization ─────────────────────────────

    def optimize(self) -> dict:
        """Stage 5: Report optimization status and detect regressions."""
        self._state.stage = max(self._state.stage, 5)
        self._save()
        return self.report()

    # ── Reporting ─────────────────────────────────────────

    def report(self) -> dict:
        """Full progress report on algorithmization."""
        return {
            "stage": self._state.stage_name,
            "total_requests": self._state.total_requests,
            "deterministic_ratio": f"{self._state.deterministic_ratio:.1%}",
            "llm_requests": self._state.llm_requests,
            "deterministic_requests": self._state.deterministic_requests,
            "patterns_found": len(self._state.patterns),
            "rules_active": sum(1 for r in self._state.rules if r.active),
            "total_cost_usd": self._state.total_cost_usd,
            "saved_cost_usd": self._state.saved_cost_usd,
            "top_patterns": [
                {
                    "id": p.id,
                    "frequency": p.frequency,
                    "cost_per_call": p.avg_cost_usd,
                    "has_rule": p.rule_generated,
                }
                for p in self._state.patterns[:5]
            ],
        }

    # ── Persistence ───────────────────────────────────────

    def _load(self):
        state_file = self._store / "state.yaml"
        if state_file.exists():
            try:
                data = yaml.safe_load(state_file.read_text()) or {}
                self._state.stage = data.get("stage", 0)
                self._state.total_requests = data.get("total_requests", 0)
                self._state.deterministic_requests = data.get("deterministic_requests", 0)
                self._state.llm_requests = data.get("llm_requests", 0)
                self._state.total_cost_usd = data.get("total_cost_usd", 0.0)
                self._state.saved_cost_usd = data.get("saved_cost_usd", 0.0)
            except Exception:
                pass

    def _save(self):
        self._store.mkdir(parents=True, exist_ok=True)
        state_file = self._store / "state.yaml"
        data = {
            "stage": self._state.stage,
            "total_requests": self._state.total_requests,
            "deterministic_requests": self._state.deterministic_requests,
            "llm_requests": self._state.llm_requests,
            "total_cost_usd": self._state.total_cost_usd,
            "saved_cost_usd": self._state.saved_cost_usd,
            "patterns_count": len(self._state.patterns),
            "rules_count": len(self._state.rules),
        }
        state_file.write_text(yaml.dump(data, default_flow_style=False))
