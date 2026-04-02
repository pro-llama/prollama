"""Integrations module for prollama."""

from __future__ import annotations

# Planfile integration
try:
    from prollama.integrations.planfile import (
        PlanfileAdapter,
        create_prollama_ticket,
        is_planfile_available,
    )
    PLANFILE_AVAILABLE = True
except ImportError:
    PLANFILE_AVAILABLE = False
    PlanfileAdapter = None
    create_prollama_ticket = None
    is_planfile_available = None

__all__ = [
    "PlanfileAdapter",
    "create_prollama_ticket",
    "is_planfile_available",
    "PLANFILE_AVAILABLE",
]
