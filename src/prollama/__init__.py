"""prollama — Intelligent LLM Execution Layer for developer teams.

Anonymize code, route models intelligently, solve tickets autonomously.
"""

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path


def _load_version() -> str:
    try:
        return package_version("prollama")
    except PackageNotFoundError:
        version_file = Path(__file__).resolve().parents[2] / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return "0.2.0"


__version__ = _load_version()
__all__ = ["Config", "Proxy", "TaskExecutor", "Anonymizer"]

from prollama.config import Config
