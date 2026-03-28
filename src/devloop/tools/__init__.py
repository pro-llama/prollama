"""Tool discovery — detect which devloop tools are installed.

Each tool is optional. The library works with whatever is available,
gracefully degrading when tools are missing.
"""

from __future__ import annotations

import importlib
import shutil
from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolStatus:
    name: str
    installed: bool
    version: Optional[str] = None
    cli_available: bool = False
    import_path: Optional[str] = None

    @property
    def emoji(self) -> str:
        return "\u2705" if self.installed else "\u274c"

    def __str__(self) -> str:
        ver = f" v{self.version}" if self.version else ""
        cli = " (CLI)" if self.cli_available else ""
        return f"{self.emoji} {self.name}{ver}{cli}"


TOOL_REGISTRY: dict[str, dict] = {
    "proxym": {
        "import": "proxym",
        "cli": "proxym",
        "role": "LLM gateway + routing + budget",
    },
    "planfile": {
        "import": "planfile",
        "cli": "planfile",
        "role": "Sprint planning + ticket management",
    },
    "llx": {
        "import": "llx",
        "cli": "llx",
        "role": "Metric-driven model selection + MCP",
    },
    "code2llm": {
        "import": "code2llm",
        "cli": "code2llm",
        "role": "Static analysis + .toon diagnostics",
    },
    "vallm": {
        "import": "vallm",
        "cli": "vallm",
        "role": "Code validation (syntax + semantic)",
    },
    "redup": {
        "import": "redup",
        "cli": "redup",
        "role": "Duplication detection + refactoring",
    },
}


def discover_tools() -> dict[str, ToolStatus]:
    """Check which tools are available."""
    results = {}
    for name, info in TOOL_REGISTRY.items():
        status = ToolStatus(name=name, installed=False, import_path=info["import"])
        try:
            mod = importlib.import_module(info["import"])
            status.installed = True
            status.version = getattr(mod, "__version__", None)
        except ImportError:
            pass
        status.cli_available = shutil.which(info["cli"]) is not None
        results[name] = status
    return results


def require_tool(name: str) -> None:
    """Raise helpful error if a tool is missing."""
    tools = discover_tools()
    if name not in tools or not tools[name].installed:
        install_cmd = f"pip install {name}"
        if name in ("code2llm", "vallm", "redup"):
            install_cmd = f"pip install devloop[analysis]"
        raise ImportError(
            f"{name} is not installed.\n"
            f"Install it with: {install_cmd}\n"
            f"Or install everything: pip install devloop[all]"
        )


def get_tool_module(name: str):
    """Import and return a tool module, or None if unavailable."""
    try:
        return importlib.import_module(TOOL_REGISTRY[name]["import"])
    except (ImportError, KeyError):
        return None
