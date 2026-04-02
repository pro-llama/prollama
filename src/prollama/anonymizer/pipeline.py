"""Three-layer anonymization pipeline: regex → NLP → AST.

NLP (Presidio) and AST (tree-sitter) layers are optional and loaded only
when their dependencies are installed.
"""

from __future__ import annotations

from prollama.anonymizer.regex_layer import RegexAnonymizer
from prollama.models import AnonymizationMapping, AnonymizationResult, PrivacyLevel


class AnonymizationPipeline:
    """Orchestrate the anonymization layers according to privacy level."""

    def __init__(self, privacy_level: PrivacyLevel = PrivacyLevel.BASIC) -> None:
        self.privacy_level = privacy_level
        self._regex = RegexAnonymizer()

    def run(self, code: str, language: str = "python") -> AnonymizationResult:
        """Run anonymization pipeline and return result with mappings."""
        if self.privacy_level == PrivacyLevel.NONE:
            return AnonymizationResult(anonymized_code=code, privacy_level=PrivacyLevel.NONE)

        all_mappings: list[AnonymizationMapping] = []
        current = code

        # Layer 1 — regex (always)
        current, regex_mappings = self._regex.anonymize(current)
        all_mappings.extend(regex_mappings)

        # Layer 2 — NLP / PII detection (full mode)
        # Uses Presidio if installed, otherwise heuristic fallback
        if self.privacy_level == PrivacyLevel.FULL:
            current, nlp_mappings = self._run_nlp(current)
            all_mappings.extend(nlp_mappings)

        # Layer 3 — AST / tree-sitter (full mode)
        if self.privacy_level == PrivacyLevel.FULL:
            try:
                current, ast_mappings = self._run_ast(current, language)
                all_mappings.extend(ast_mappings)
            except ImportError:
                pass  # tree-sitter not installed — skip silently

        # Stats summary
        stats: dict[str, int] = {}
        for m in all_mappings:
            stats[m.category] = stats.get(m.category, 0) + 1

        return AnonymizationResult(
            anonymized_code=current,
            mappings=all_mappings,
            stats=stats,
            privacy_level=self.privacy_level,
        )

    def rehydrate(self, code: str, mappings: list[AnonymizationMapping]) -> str:
        """Reverse anonymization using stored mappings.

        AST_IDENT mappings are deduplicated (one entry per unique identifier)
        so we replace ALL occurrences. Regex/NLP mappings have unique tokens
        per occurrence, so we replace exactly one.
        """
        result = code
        # Process AST mappings first (replace all), then regex/NLP (replace one).
        # Sort by replacement length descending to avoid partial matches.
        ast_mappings = sorted(
            [m for m in mappings if m.category == "AST_IDENT"],
            key=lambda m: len(m.replacement),
            reverse=True,
        )
        other_mappings = [m for m in mappings if m.category != "AST_IDENT"]

        for mapping in ast_mappings:
            result = result.replace(mapping.replacement, mapping.original)
        for mapping in reversed(other_mappings):
            result = result.replace(mapping.replacement, mapping.original, 1)
        return result

    # ------------------------------------------------------------------
    # Optional layer stubs (real implementations require extra deps)
    # ------------------------------------------------------------------

    @staticmethod
    def _run_nlp(code: str) -> tuple[str, list[AnonymizationMapping]]:
        """NLP-based PII detection. Uses Presidio if installed, else heuristic fallback."""
        from prollama.anonymizer.nlp_layer import NLPAnonymizer

        anonymizer = NLPAnonymizer()
        return anonymizer.anonymize(code)

    @staticmethod
    def _run_ast(code: str, language: str) -> tuple[str, list[AnonymizationMapping]]:
        """AST-based identifier anonymization via tree-sitter. Requires `prollama[ast]`."""
        from prollama.anonymizer.ast_layer import ASTAnonymizer

        anonymizer = ASTAnonymizer(language=language)
        return anonymizer.anonymize(code)
