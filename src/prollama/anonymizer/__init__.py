"""Code anonymization pipeline — regex, NLP, AST layers."""

from prollama.anonymizer.pipeline import AnonymizationPipeline
from prollama.anonymizer.regex_layer import RegexAnonymizer

__all__ = ["RegexAnonymizer", "AnonymizationPipeline"]

# Optional: AST layer (requires tree-sitter)
try:
    from prollama.anonymizer.ast_layer import ASTAnonymizer  # noqa: F401

    __all__.append("ASTAnonymizer")
except ImportError:
    pass
