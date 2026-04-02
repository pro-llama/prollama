"""Enhanced anonymization layer with Tabnine Shield-like content filtering.

Combines AST-based identifier anonymization with regex pattern matching and
entropy analysis to provide comprehensive protection against secrets and PII leakage.

This is a two-stage filtering system:
1. Input Filtering: Before processing by AI models
2. Output Filtering: Before displaying results to users
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from prollama.models import AnonymizationMapping
from prollama.security.content_filter import ContentFilter, DataType, SeverityLevel


@dataclass
class EnhancedAnonymizationMapping:
    """Enhanced anonymization mapping with additional metadata."""
    original: str
    replacement: str
    category: str  # SECRET, EMAIL, PII, AST_IDENT, ...
    position: tuple[int, int] | None = None  # (start, end) if known
    data_type: DataType = DataType.API_KEY
    severity: SeverityLevel = SeverityLevel.MEDIUM
    pattern_name: str = ""
    confidence: float = 0.0
    context: str = ""


class EnhancedAnonymizer:
    """Enhanced anonymizer combining AST analysis with content filtering."""
    
    def __init__(self, language: str = "python"):
        """Initialize enhanced anonymizer.
        
        Args:
            language: Programming language to process
        """
        self.language = language
        self.content_filter = ContentFilter()
        self.mappings: List[EnhancedAnonymizationMapping] = []
        self._replacement_counter = 0
        
    def anonymize(self, code: str, filter_secrets: bool = True) -> Tuple[str, List[EnhancedAnonymizationMapping]]:
        """Anonymize code using both AST analysis and content filtering.
        
        Args:
            code: Source code to anonymize
            filter_secrets: Whether to apply secret/PII filtering
            
        Returns:
            Tuple of (anonymized_code, mappings)
        """
        self.mappings = []
        anonymized_code = code
        
        # Stage 1: Content filtering for secrets and PII
        if filter_secrets:
            anonymized_code = self._apply_content_filtering(anonymized_code)
        
        # Stage 2: AST-based identifier anonymization
        try:
            anonymized_code = self._apply_ast_anonymization(anonymized_code)
        except ImportError:
            # Fallback if tree-sitter not available
            anonymized_code = self._apply_fallback_anonymization(anonymized_code)
        
        return anonymized_code, self.mappings
    
    def _apply_content_filtering(self, code: str) -> str:
        """Apply content filtering for secrets and PII."""
        detections = self.content_filter.filter_content(code)
        
        for detection in detections:
            # Create enhanced mapping
            mapping = EnhancedAnonymizationMapping(
                original=detection.matched_text,
                replacement=self._get_replacement(detection),
                category=detection.data_type.value.upper(),
                position=(detection.start_pos, detection.end_pos),
                data_type=detection.data_type,
                severity=detection.severity,
                pattern_name=detection.pattern_name,
                confidence=detection.confidence,
                context=detection.context
            )
            
            self.mappings.append(mapping)
        
        # Sanitize the code
        return self.content_filter.sanitize_content(code, detections)
    
    def _apply_ast_anonymization(self, code: str) -> str:
        """Apply AST-based identifier anonymization."""
        try:
            import tree_sitter
        except ImportError:
            raise ImportError("AST anonymization requires tree-sitter. Install with: pip install prollama[ast]")
        
        # Import AST anonymizer components
        from prollama.anonymizer.ast_layer import (
            LANGUAGE_TARGETS, PYTHON_TARGETS, LANGUAGE_BUILTINS, PYTHON_BUILTINS
        )
        
        parser = tree_sitter.Parser()
        ts_language = self._get_language()
        parser.language = ts_language

        code_bytes = code.encode("utf-8")
        tree = parser.parse(code_bytes)
        root = tree.root_node

        # Collect all identifiers to anonymize
        replacements: List[Tuple[int, int, str, str]] = []
        self._walk_tree(root, code_bytes, replacements)

        # Apply replacements
        for start, end, original, replacement in replacements:
            mapping = EnhancedAnonymizationMapping(
                original=original,
                replacement=replacement,
                category="AST_IDENT",
                position=(start, end),
                data_type=DataType.API_KEY,  # Using as placeholder for identifiers
                severity=SeverityLevel.LOW,
                pattern_name="ast_identifier",
                confidence=0.9
            )
            self.mappings.append(mapping)

        return self._apply_replacements(code_bytes, replacements).decode("utf-8")
    
    def _apply_fallback_anonymization(self, code: str) -> str:
        """Fallback anonymization using regex when AST not available."""
        # Simple regex-based identifier anonymization
        identifier_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')
        
        def replace_identifier(match):
            identifier = match.group(1)
            
            # Skip common keywords and built-ins
            if identifier in ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'for', 'while', 'try', 'except', 'with', 'as']:
                return identifier
            
            # Skip very short identifiers
            if len(identifier) <= 2:
                return identifier
            
            # Skip all-caps constants
            if identifier.isupper():
                return identifier
            
            # Generate replacement
            replacement = f"var_{self._replacement_counter}"
            self._replacement_counter += 1
            
            mapping = EnhancedAnonymizationMapping(
                original=identifier,
                replacement=replacement,
                category="FALLBACK_IDENT",
                position=(match.start(), match.end()),
                data_type=DataType.API_KEY,  # Placeholder
                severity=SeverityLevel.LOW,
                pattern_name="fallback_identifier",
                confidence=0.7
            )
            self.mappings.append(mapping)
            
            return replacement
        
        return identifier_pattern.sub(replace_identifier, code)
    
    def _get_language(self):
        """Get tree-sitter language parser."""
        try:
            import tree_sitter_python
            return tree_sitter_python.language()
        except ImportError:
            try:
                import tree_sitter
                return tree_sitter.Language(self._get_language_library(), self.language)
            except Exception as e:
                raise ImportError(f"Could not load tree-sitter language for {self.language}: {e}")
    
    def _get_language_library(self) -> str:
        """Get path to language library."""
        # Try common locations
        possible_paths = [
            f"/usr/local/lib/tree-sitter/{self.language}.so",
            f"/usr/lib/tree-sitter/{self.language}.so",
            f"{Path.home()}/.local/lib/tree-sitter/{self.language}.so",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        raise FileNotFoundError(f"Tree-sitter library for {self.language} not found")
    
    def _walk_tree(self, node, source: bytes, replacements: List[Tuple[int, int, str, str]]) -> None:
        """Walk AST tree and collect identifier replacements."""
        from prollama.anonymizer.ast_layer import LANGUAGE_TARGETS, LANGUAGE_BUILTINS
        
        targets = LANGUAGE_TARGETS.get(self.language, {})
        builtins = LANGUAGE_BUILTINS.get(self.language, set())

        if node.type in targets:
            text = source[node.start_byte:node.end_byte].decode("utf-8")

            # Skip if it's a builtin/protected identifier
            if text in builtins:
                return

            # Skip single-character identifiers
            if len(text) <= 1:
                return

            # Skip identifiers that are all uppercase and short (constants)
            if text.isupper() and len(text) <= 6:
                return

            # Skip dunder methods
            if text.startswith("__") and text.endswith("__"):
                return

            # Get replacement
            replacement = f"var_{self._replacement_counter}"
            self._replacement_counter += 1
            
            replacements.append((node.start_byte, node.end_byte, text, replacement))

        # Recursively walk children
        for child in node.children:
            self._walk_tree(child, source, replacements)
    
    def _apply_replacements(self, code_bytes: bytes, replacements: List[Tuple[int, int, str, str]]) -> bytes:
        """Apply replacements to code bytes."""
        # Sort by position descending to avoid offset issues
        replacements.sort(key=lambda x: x[0], reverse=True)

        for start, end, original, replacement in replacements:
            code_bytes = (
                code_bytes[:start] + 
                replacement.encode("utf-8") + 
                code_bytes[end:]
            )

        return code_bytes
    
    def _get_replacement(self, detection) -> str:
        """Get appropriate replacement for detected sensitive data."""
        data_type = detection.data_type
        
        replacements = {
            DataType.API_KEY: f"[API_KEY_{self._replacement_counter}]",
            DataType.PASSWORD: f"[PASSWORD_{self._replacement_counter}]",
            DataType.TOKEN: f"[TOKEN_{self._replacement_counter}]",
            DataType.SSH_KEY: f"[SSH_KEY_{self._replacement_counter}]",
            DataType.EMAIL: f"[EMAIL_{self._replacement_counter}]",
            DataType.CREDIT_CARD: f"[CREDIT_CARD_{self._replacement_counter}]",
            DataType.PHONE: f"[PHONE_{self._replacement_counter}]",
            DataType.SSN: f"[SSN_{self._replacement_counter}]",
            DataType.SECRET_KEY: f"[SECRET_KEY_{self._replacement_counter}]",
            DataType.CERTIFICATE: f"[CERTIFICATE_{self._replacement_counter}]",
            DataType.HIGH_ENTROPY: f"[HIGH_ENTROPY_{self._replacement_counter}]",
        }
        
        self._replacement_counter += 1
        return replacements.get(data_type, f"[SENSITIVE_DATA_{self._replacement_counter}]")
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        if not self.mappings:
            return {"status": "clean", "detections": 0}
        
        # Group by severity
        by_severity = {}
        for severity in SeverityLevel:
            by_severity[severity.value] = [
                m for m in self.mappings if m.severity == severity
            ]
        
        # Group by data type
        by_data_type = {}
        for data_type in DataType:
            by_data_type[data_type.value] = [
                m for m in self.mappings if m.data_type == data_type
            ]
        
        # Calculate risk score
        risk_score = self._calculate_risk_score()
        
        return {
            "status": "flagged" if any(by_severity["critical"] + by_severity["high"]) else "warning",
            "total_detections": len(self.mappings),
            "risk_score": risk_score,
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_data_type": {k: len(v) for k, v in by_data_type.items()},
            "critical_detections": len(by_severity["critical"]),
            "high_detections": len(by_severity["high"]),
            "recommendations": self._generate_recommendations(by_severity)
        }
    
    def _calculate_risk_score(self) -> float:
        """Calculate overall risk score (0-100)."""
        if not self.mappings:
            return 0.0
        
        severity_weights = {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 10,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 1,
        }
        
        total_score = sum(
            severity_weights[mapping.severity] * mapping.confidence 
            for mapping in self.mappings
        )
        
        # Normalize to 0-100 scale
        return min(100.0, total_score)
    
    def _generate_recommendations(self, by_severity: Dict[str, List]) -> List[str]:
        """Generate security recommendations based on detections."""
        recommendations = []
        
        if by_severity["critical"]:
            recommendations.append(
                f"🚨 CRITICAL: {len(by_severity['critical'])} critical security issues detected. "
                "Immediate action required."
            )
        
        if by_severity["high"]:
            recommendations.append(
                f"⚠️  HIGH: {len(by_severity['high'])} high-risk items detected. "
                "Review and remediate promptly."
            )
        
        if by_severity["medium"]:
            recommendations.append(
                f"🔍 MEDIUM: {len(by_severity['medium'])} medium-risk items detected. "
                "Consider reviewing for potential security improvements."
            )
        
        # Specific recommendations based on data types
        data_types_present = set(mapping.data_type for mapping in self.mappings)
        
        if DataType.API_KEY in data_types_present:
            recommendations.append("🔑 API keys detected - ensure they are rotated and properly secured.")
        
        if DataType.EMAIL in data_types_present:
            recommendations.append("📧 Email addresses detected - consider if PII exposure is necessary.")
        
        if DataType.CREDIT_CARD in data_types_present:
            recommendations.append("💳 Credit card numbers detected - immediate PCI compliance review required.")
        
        return recommendations
    
    def print_security_report(self) -> None:
        """Print formatted security report."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        
        console = Console()
        report = self.get_security_report()
        
        if report["status"] == "clean":
            console.print("[green]✓ Security Scan Complete - No issues detected[/green]")
            return
        
        # Create summary table
        table = Table(title="Security Analysis Summary")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        
        table.add_row("Total Detections", str(report["total_detections"]))
        table.add_row("Risk Score", f"{report['risk_score']:.1f}/100")
        table.add_row("Critical Issues", str(report["critical_detections"]))
        table.add_row("High Risk Issues", str(report["high_detections"]))
        
        console.print(table)
        
        # Show recommendations
        if report["recommendations"]:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in report["recommendations"]:
                console.print(f"  {rec}")


# Convenience function for quick usage
def anonymize_code(code: str, language: str = "python", filter_secrets: bool = True) -> Tuple[str, List[EnhancedAnonymizationMapping]]:
    """Quick function to anonymize code with enhanced filtering.
    
    Args:
        code: Source code to anonymize
        language: Programming language
        filter_secrets: Whether to apply secret/PII filtering
        
    Returns:
        Tuple of (anonymized_code, mappings)
    """
    anonymizer = EnhancedAnonymizer(language)
    return anonymizer.anonymize(code, filter_secrets)
