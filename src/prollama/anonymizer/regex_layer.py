"""Layer 1: Regex-based secret and PII detection.

Fast (<1ms), always active, catches well-known patterns for API keys,
tokens, connection strings, emails, IPs, and more.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from prollama.models import AnonymizationMapping

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

@dataclass
class SecretPattern:
    name: str
    category: str
    regex: re.Pattern[str]


# fmt: off
PATTERNS: list[SecretPattern] = [
    # Cloud provider keys
    SecretPattern("AWS Access Key",       "SECRET", re.compile(r"AKIA[0-9A-Z]{16}")),
    SecretPattern("AWS Secret Key",       "SECRET", re.compile(r"(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?")),
    SecretPattern("GCP API Key",          "SECRET", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    SecretPattern("Azure Key",            "SECRET", re.compile(r"(?i)(?:azure|az)[_\-]?(?:key|secret|token)\s*[=:]\s*['\"]?([A-Za-z0-9+/=]{20,})['\"]?")),

    # Payment / SaaS
    SecretPattern("Stripe Secret Key",    "SECRET", re.compile(r"sk_live_[0-9a-zA-Z]{24,}")),
    SecretPattern("Stripe Publishable",   "SECRET", re.compile(r"pk_live_[0-9a-zA-Z]{24,}")),
    SecretPattern("Stripe Test Key",      "SECRET", re.compile(r"sk_test_[0-9a-zA-Z]{24,}")),

    # VCS tokens
    SecretPattern("GitHub Token",         "SECRET", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    SecretPattern("GitLab Token",         "SECRET", re.compile(r"glpat-[A-Za-z0-9\-_]{20,}")),

    # Generic tokens
    SecretPattern("Bearer Token",         "SECRET", re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*")),
    SecretPattern("JWT",                  "SECRET", re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    SecretPattern("Generic API Key",      "SECRET", re.compile(r"(?i)(?:api[_\-]?key|apikey|access[_\-]?token|auth[_\-]?token)\s*[=:]\s*['\"]?([A-Za-z0-9\-._]{16,})['\"]?")),

    # Connection strings
    SecretPattern("Database URL",         "SECRET", re.compile(r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s'\"]+")),
    SecretPattern("SMTP URL",             "SECRET", re.compile(r"smtp://[^\s'\"]+")),

    # PII
    SecretPattern("Email",                "EMAIL",  re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    SecretPattern("IPv4",                 "IP",     re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    SecretPattern("Phone (intl)",         "PHONE",  re.compile(r"\+\d{1,3}[\s\-]?\d{4,14}")),

    # Private URLs
    SecretPattern("Internal URL",         "URL",    re.compile(r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)[^\s'\"]+")),
]
# fmt: on


# ---------------------------------------------------------------------------
# Anonymizer
# ---------------------------------------------------------------------------

class RegexAnonymizer:
    """Apply regex-based anonymization to source code text."""

    def __init__(self, extra_patterns: list[SecretPattern] | None = None) -> None:
        self.patterns = PATTERNS + (extra_patterns or [])
        self._counter: dict[str, int] = {}

    def _next_token(self, category: str) -> str:
        count = self._counter.get(category, 0) + 1
        self._counter[category] = count
        return f"[{category}_{count:03d}]"

    def anonymize(self, code: str) -> tuple[str, list[AnonymizationMapping]]:
        """Return (anonymized_code, mappings).

        Mappings can later be used for rehydration (restoring originals).
        """
        mappings: list[AnonymizationMapping] = []
        result = code

        for pattern in self.patterns:
            for match in pattern.regex.finditer(result):
                original = match.group(0)
                # Avoid double-replacing already-tokenized spans
                if original.startswith("[") and original.endswith("]"):
                    continue
                replacement = self._next_token(pattern.category)
                mappings.append(
                    AnonymizationMapping(
                        original=original,
                        replacement=replacement,
                        category=pattern.category,
                    )
                )
                result = result.replace(original, replacement, 1)

        return result, mappings

    def rehydrate(self, code: str, mappings: list[AnonymizationMapping]) -> str:
        """Restore original values from anonymized code using mappings."""
        result = code
        # Reverse order to handle nested replacements correctly
        for mapping in reversed(mappings):
            result = result.replace(mapping.replacement, mapping.original, 1)
        return result

    def reset(self) -> None:
        """Reset internal counters (call between independent documents)."""
        self._counter.clear()
