"""Layer 2: NLP-based PII detection in comments and string literals.

If Presidio is installed (`prollama[nlp]`), uses the full Presidio engine.
Otherwise, falls back to a lightweight heuristic detector for common PII
patterns in code comments and docstrings.
"""

from __future__ import annotations

import re

from prollama.models import AnonymizationMapping

# ---------------------------------------------------------------------------
# Lightweight fallback PII detector (no ML dependencies)
# ---------------------------------------------------------------------------

# Patterns targeting PII typically found in code comments and strings
COMMENT_PII_PATTERNS = [
    # Person names in common code comment patterns
    (
        "PERSON",
        re.compile(
            r"(?:(?:Author|Maintainer|Contact|Owner|Assigned to)"
            r"\s*[:=]\s*|"
            r"(?:Created by|Modified by|Fixed by|Written by|Reviewed by)"
            r"\s*[:=]?\s*)"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            re.MULTILINE,
        ),
        1,  # capture group index
    ),
    # Person names in @author tags
    (
        "PERSON",
        re.compile(
            r"@author\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",
            re.MULTILINE,
        ),
        1,
    ),
    # Copyright with person names
    (
        "PERSON",
        re.compile(
            r"[Cc]opyright\s+(?:\(c\)\s*)?(?:\d{4}(?:\s*[-–]\s*\d{4})?\s+)?"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        ),
        1,
    ),
    # Postal / street addresses (common patterns)
    (
        "ADDRESS",
        re.compile(
            r"\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,3}"
            r"\s+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl)"
            r"\.?",
        ),
        0,
    ),
    # US Social Security Numbers
    (
        "SSN",
        re.compile(r"\b\d{3}[-–]\d{2}[-–]\d{4}\b"),
        0,
    ),
    # Credit card numbers (basic Luhn-candidate patterns)
    (
        "CREDIT_CARD",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        0,
    ),
    # Dates that might be personal (DD/MM/YYYY, MM/DD/YYYY, etc.)
    (
        "DATE",
        re.compile(
            r"(?:date\s*(?:of\s*birth|born)|DOB|birthday)\s*[:=]\s*"
            r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            re.IGNORECASE,
        ),
        1,
    ),
]


class NLPAnonymizer:
    """Detect and anonymize PII in code comments and string literals.

    Uses Presidio if available, otherwise falls back to regex heuristics.
    """

    def __init__(self) -> None:
        self._counter: dict[str, int] = {}
        self._use_presidio = self._check_presidio()

    def anonymize(self, code: str) -> tuple[str, list[AnonymizationMapping]]:
        """Detect and replace PII in the given text."""
        if self._use_presidio:
            return self._anonymize_presidio(code)
        return self._anonymize_heuristic(code)

    def reset(self) -> None:
        self._counter.clear()

    # -- Presidio path ------------------------------------------------------

    @staticmethod
    def _check_presidio() -> bool:
        try:
            import presidio_analyzer  # noqa: F401
            return True
        except ImportError:
            return False

    def _anonymize_presidio(self, code: str) -> tuple[str, list[AnonymizationMapping]]:
        """Use Presidio for PII detection."""
        from presidio_analyzer import AnalyzerEngine

        analyzer = AnalyzerEngine()

        # Detect PII
        results = analyzer.analyze(
            text=code,
            language="en",
            entities=[
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
                "CREDIT_CARD", "US_SSN", "LOCATION",
                "IP_ADDRESS", "IBAN_CODE",
            ],
        )

        if not results:
            return code, []

        # Build reversible mappings
        mappings: list[AnonymizationMapping] = []

        for r in results:
            original = code[r.start:r.end]
            category = r.entity_type
            replacement = self._next_token(category)
            mappings.append(
                AnonymizationMapping(
                    original=original,
                    replacement=replacement,
                    category=category,
                    position=(0, r.start),
                )
            )

        # Apply replacements manually (Presidio's built-in anonymizer
        # doesn't produce stable reversible tokens)
        result = code
        for mapping in sorted(mappings, key=lambda m: (m.position or (0, 0))[1], reverse=True):
            result = result[:result.find(mapping.original)] + mapping.replacement + result[result.find(mapping.original) + len(mapping.original):]

        return result, mappings

    # -- Heuristic fallback -------------------------------------------------

    def _anonymize_heuristic(self, code: str) -> tuple[str, list[AnonymizationMapping]]:
        """Regex-based PII detection fallback."""
        mappings: list[AnonymizationMapping] = []
        result = code

        for category, pattern, group_idx in COMMENT_PII_PATTERNS:
            for match in pattern.finditer(result):
                original = match.group(group_idx)
                if not original or len(original) < 3:
                    continue

                replacement = self._next_token(category)
                mappings.append(
                    AnonymizationMapping(
                        original=original,
                        replacement=replacement,
                        category=category,
                    )
                )
                result = result.replace(original, replacement, 1)

        return result, mappings

    def _next_token(self, category: str) -> str:
        count = self._counter.get(category, 0) + 1
        self._counter[category] = count
        return f"[{category}_{count:03d}]"
