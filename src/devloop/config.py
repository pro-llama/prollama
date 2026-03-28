"""Configuration — one file to rule them all.

Reads from (in priority order):
    1. Environment variables (DEVLOOP_*, PROXYM_*, etc.)
    2. ./devloop.yaml
    3. ~/.config/devloop/config.yaml
    4. Sensible defaults (everything works out of the box)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ProxyConfig:
    """Proxym gateway settings."""

    url: str = "http://localhost:4000"
    api_key: str = ""
    default_tier: str = "balanced"
    budget_daily_usd: float = 3.0
    budget_monthly_usd: float = 60.0

    @classmethod
    def from_env(cls) -> ProxyConfig:
        return cls(
            url=os.getenv("PROXYM_URL", "http://localhost:4000"),
            api_key=os.getenv("PROXYM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            default_tier=os.getenv("PROXYM_DEFAULT_TIER", "balanced"),
            budget_daily_usd=float(os.getenv("PROXYM_DAILY_BUDGET", "3.0")),
            budget_monthly_usd=float(os.getenv("PROXYM_MONTHLY_BUDGET", "60.0")),
        )


@dataclass
class TicketConfig:
    """Planfile ticket system settings."""

    backend: str = "local"  # local | github | jira | gitlab
    github_token: str = ""
    github_repo: str = ""
    jira_url: str = ""
    jira_token: str = ""
    auto_sync: bool = False

    @classmethod
    def from_env(cls) -> TicketConfig:
        return cls(
            backend=os.getenv("PLANFILE_BACKEND", "local"),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
            jira_url=os.getenv("JIRA_URL", ""),
            jira_token=os.getenv("JIRA_TOKEN", ""),
            auto_sync=os.getenv("PLANFILE_AUTO_SYNC", "").lower() in ("1", "true"),
        )


@dataclass
class AnalysisConfig:
    """Code analysis tool settings."""

    cc_target: float = 3.5
    max_cc: int = 15
    vallm_pass_target: float = 0.90
    formats: list[str] = field(default_factory=lambda: ["toon", "evolution"])

    @classmethod
    def from_env(cls) -> AnalysisConfig:
        return cls(
            cc_target=float(os.getenv("DEVLOOP_CC_TARGET", "3.5")),
            max_cc=int(os.getenv("DEVLOOP_MAX_CC", "15")),
            vallm_pass_target=float(os.getenv("DEVLOOP_VALLM_TARGET", "0.90")),
        )


@dataclass
class Config:
    """Unified config for the entire devloop stack."""

    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    tickets: TicketConfig = field(default_factory=TicketConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    project_path: str = "."
    verbose: bool = False

    @classmethod
    def load(cls, path: Optional[str] = None) -> Config:
        """Load config: YAML file → env vars → defaults."""
        cfg = cls()
        cfg.proxy = ProxyConfig.from_env()
        cfg.tickets = TicketConfig.from_env()
        cfg.analysis = AnalysisConfig.from_env()
        cfg.verbose = os.getenv("DEVLOOP_VERBOSE", "").lower() in ("1", "true")

        yaml_path = _find_config(path)
        if yaml_path:
            cfg = _merge_yaml(cfg, yaml_path)

        return cfg

    def save(self, path: Optional[str] = None) -> Path:
        """Save current config to devloop.yaml."""
        target = Path(path or "./devloop.yaml")
        data = {
            "proxy": {
                "url": self.proxy.url,
                "default_tier": self.proxy.default_tier,
                "budget_daily_usd": self.proxy.budget_daily_usd,
                "budget_monthly_usd": self.proxy.budget_monthly_usd,
            },
            "tickets": {
                "backend": self.tickets.backend,
                "auto_sync": self.tickets.auto_sync,
            },
            "analysis": {
                "cc_target": self.analysis.cc_target,
                "max_cc": self.analysis.max_cc,
                "vallm_pass_target": self.analysis.vallm_pass_target,
                "formats": self.analysis.formats,
            },
        }
        target.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return target


def _find_config(explicit: Optional[str] = None) -> Optional[Path]:
    """Search for config file in standard locations."""
    candidates = [
        Path(explicit) if explicit else None,
        Path("./devloop.yaml"),
        Path("./devloop.yml"),
        Path.home() / ".config" / "devloop" / "config.yaml",
    ]
    for p in candidates:
        if p and p.exists():
            return p
    return None


def _merge_yaml(cfg: Config, path: Path) -> Config:
    """Merge YAML values into config (env vars take precedence)."""
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception:
        return cfg

    proxy = data.get("proxy", {})
    if not os.getenv("PROXYM_URL") and "url" in proxy:
        cfg.proxy.url = proxy["url"]
    if "default_tier" in proxy:
        cfg.proxy.default_tier = proxy["default_tier"]

    tickets = data.get("tickets", {})
    if not os.getenv("PLANFILE_BACKEND") and "backend" in tickets:
        cfg.tickets.backend = tickets["backend"]

    analysis = data.get("analysis", {})
    if "cc_target" in analysis:
        cfg.analysis.cc_target = analysis["cc_target"]
    if "formats" in analysis:
        cfg.analysis.formats = analysis["formats"]

    return cfg
