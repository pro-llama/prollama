"""
Prollama - Progressive algorithmization toolchain

From LLM to deterministic code, from proxy to tickets.
"""

__version__ = "0.1.2"
__author__ = "Tom Sapletta"
__email__ = "tom@sapletta.com"

from .core import ProllamaCore
from .llm import LLMInterface
from .proxy import ProxyManager
from .tickets import TicketManager

__all__ = [
    "ProllamaCore",
    "LLMInterface", 
    "ProxyManager",
    "TicketManager",
]
