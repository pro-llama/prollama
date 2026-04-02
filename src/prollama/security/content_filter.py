"""Content filtering module similar to Tabnine Shield.

Detects secrets, PII, and sensitive data using regex patterns and entropy analysis.
Provides two-stage filtering: input filtering (before AI processing) and 
output filtering (before displaying results).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

from rich.console import Console


class SeverityLevel(Enum):
    """Severity levels for detected sensitive data."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataType(Enum):
    """Types of sensitive data that can be detected."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    SSH_KEY = "ssh_key"
    EMAIL = "email"
    CREDIT_CARD = "credit_card"
    PHONE = "phone"
    SSN = "ssn"
    SECRET_KEY = "secret_key"
    CERTIFICATE = "certificate"
    HIGH_ENTROPY = "high_entropy"


@dataclass
class DetectionResult:
    """Result of sensitive data detection."""
    data_type: DataType
    severity: SeverityLevel
    matched_text: str
    start_pos: int
    end_pos: int
    pattern_name: str
    confidence: float
    context: str = ""


class ContentFilter:
    """Content filtering system similar to Tabnine Shield."""
    
    def __init__(self):
        """Initialize content filter with regex patterns and entropy thresholds."""
        self.console = Console()
        self._setup_patterns()
        self._setup_entropy_thresholds()
    
    def _setup_patterns(self) -> None:
        """Setup regex patterns for detecting sensitive data."""
        self.patterns = {
            # AWS Keys
            "aws_access_key": {
                "pattern": re.compile(r'(?i)aws_(access_key_id|secret_access_key).{0,30}[0-9a-zA-Z/+]{40}'),
                "data_type": DataType.API_KEY,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.95,
            },
            
            # AWS Secret Access Key (standalone)
            "aws_secret_key": {
                "pattern": re.compile(r'[A-Z0-9/+]{40}'),
                "data_type": DataType.SECRET_KEY,
                "severity": SeverityLevel.HIGH,
                "confidence": 0.7,
            },
            
            # GitHub Token
            "github_token": {
                "pattern": re.compile(r'ghp_[a-zA-Z0-9]{36}'),
                "data_type": DataType.TOKEN,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.95,
            },
            
            # GitHub App Token
            "github_app_token": {
                "pattern": re.compile(r'(ghs|ghr)_[a-zA-Z0-9]{36}'),
                "data_type": DataType.TOKEN,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.95,
            },
            
            # Bearer Tokens
            "bearer_token": {
                "pattern": re.compile(r'(?i)bearer\s+[a-zA-Z0-9._\-]{20,}'),
                "data_type": DataType.TOKEN,
                "severity": SeverityLevel.HIGH,
                "confidence": 0.8,
            },
            
            # SSH Private Keys
            "ssh_private_key": {
                "pattern": re.compile(r'-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----'),
                "data_type": DataType.SSH_KEY,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.95,
            },
            
            # Email addresses
            "email": {
                "pattern": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
                "data_type": DataType.EMAIL,
                "severity": SeverityLevel.MEDIUM,
                "confidence": 0.9,
            },
            
            # Credit Card Numbers
            "credit_card": {
                "pattern": re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
                "data_type": DataType.CREDIT_CARD,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.85,
            },
            
            # Phone Numbers (various formats)
            "phone_us": {
                "pattern": re.compile(r'(\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
                "data_type": DataType.PHONE,
                "severity": SeverityLevel.MEDIUM,
                "confidence": 0.7,
            },
            
            "phone_international": {
                "pattern": re.compile(r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
                "data_type": DataType.PHONE,
                "severity": SeverityLevel.MEDIUM,
                "confidence": 0.6,
            },
            
            # Social Security Numbers
            "ssn": {
                "pattern": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                "data_type": DataType.SSN,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.9,
            },
            
            # Generic API Keys (common patterns)
            "api_key_generic": {
                "pattern": re.compile(r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?key)[\s:=]+["\']?[a-zA-Z0-9_\-\.]{16,}["\']?'),
                "data_type": DataType.API_KEY,
                "severity": SeverityLevel.HIGH,
                "confidence": 0.8,
            },
            
            # JWT Tokens
            "jwt_token": {
                "pattern": re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
                "data_type": DataType.TOKEN,
                "severity": SeverityLevel.HIGH,
                "confidence": 0.85,
            },
            
            # Private Keys and Certificates
            "private_key_pem": {
                "pattern": re.compile(r'-----BEGIN\s+(PRIVATE\s+KEY|CERTIFICATE)-----'),
                "data_type": DataType.SECRET_KEY,
                "severity": SeverityLevel.CRITICAL,
                "confidence": 0.95,
            },
            
            # Database URLs
            "database_url": {
                "pattern": re.compile(r'(?i)(mysql|postgresql|mongodb|redis)://[^\s:]+:[^\s@]+@[^\s/]+'),
                "data_type": DataType.SECRET_KEY,
                "severity": SeverityLevel.HIGH,
                "confidence": 0.8,
            },
            
            # Slack Tokens
            "slack_token": {
                "pattern": re.compile(r'xox[baprs]-[a-zA-Z0-9-]+'),
                "data_type": DataType.TOKEN,
                "severity": SeverityLevel.HIGH,
                "confidence": 0.9,
            },
        }
    
    def _setup_entropy_thresholds(self) -> None:
        """Setup entropy thresholds for high-entropy string detection."""
        self.entropy_thresholds = {
            "very_high": 4.5,  # Likely cryptographic keys
            "high": 4.0,       # Possible secrets
            "medium": 3.5,     # Worth investigating
        }
    
    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string.
        
        Args:
            text: String to calculate entropy for
            
        Returns:
            Entropy value (higher = more random)
        """
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        
        for count in char_counts.values():
            probability = count / text_len
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def detect_high_entropy_strings(self, text: str, min_length: int = 20) -> List[DetectionResult]:
        """Detect high-entropy strings that might be secrets.
        
        Args:
            text: Text to analyze
            min_length: Minimum string length to consider
            
        Returns:
            List of detection results for high-entropy strings
        """
        results = []
        
        # Find all potential high-entropy strings
        # Look for alphanumeric strings with minimum length
        potential_strings = re.findall(r'[a-zA-Z0-9+/=_\-.]{' + str(min_length) + ',}', text)
        
        for string in potential_strings:
            # Skip common non-secret patterns
            if self._is_common_non_secret(string):
                continue
            
            entropy = self.calculate_entropy(string)
            
            # Determine severity based on entropy
            if entropy >= self.entropy_thresholds["very_high"]:
                severity = SeverityLevel.CRITICAL
                confidence = min(0.9, (entropy - 4.0) / 2.0)
            elif entropy >= self.entropy_thresholds["high"]:
                severity = SeverityLevel.HIGH
                confidence = min(0.7, (entropy - 3.5) / 2.0)
            elif entropy >= self.entropy_thresholds["medium"]:
                severity = SeverityLevel.MEDIUM
                confidence = min(0.5, (entropy - 3.0) / 2.0)
            else:
                continue
            
            # Find position in original text
            start_pos = text.find(string)
            if start_pos >= 0:
                results.append(DetectionResult(
                    data_type=DataType.HIGH_ENTROPY,
                    severity=severity,
                    matched_text=string,
                    start_pos=start_pos,
                    end_pos=start_pos + len(string),
                    pattern_name="high_entropy",
                    confidence=confidence,
                    context=self._get_context(text, start_pos, len(string))
                ))
        
        return results
    
    def _is_common_non_secret(self, text: str) -> bool:
        """Check if a string is likely not a secret despite high entropy."""
        # Common patterns that might have high entropy but aren't secrets
        common_patterns = [
            r'^[a-fA-F0-9]{32}$',  # MD5 hashes
            r'^[a-fA-F0-9]{40}$',  # SHA1 hashes
            r'^[a-fA-F0-9]{64}$',  # SHA256 hashes
            r'^[A-Za-z]{20,}$',    # Long words without numbers/symbols
            r'^[0-9]{20,}$',       # Long numbers only
        ]
        
        for pattern in common_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _get_context(self, text: str, start_pos: int, length: int, context_size: int = 50) -> str:
        """Get context around a detected pattern."""
        context_start = max(0, start_pos - context_size)
        context_end = min(len(text), start_pos + length + context_size)
        return text[context_start:context_end]
    
    def filter_content(self, content: str, include_high_entropy: bool = True) -> List[DetectionResult]:
        """Filter content for sensitive data using regex patterns.
        
        Args:
            content: Content to filter
            include_high_entropy: Whether to include high-entropy detection
            
        Returns:
            List of detection results
        """
        results = []
        
        # Check each regex pattern
        for pattern_name, pattern_config in self.patterns.items():
            pattern = pattern_config["pattern"]
            
            for match in pattern.finditer(content):
                # Get context for the match
                context = self._get_context(content, match.start(), len(match.group()))
                
                result = DetectionResult(
                    data_type=pattern_config["data_type"],
                    severity=pattern_config["severity"],
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    pattern_name=pattern_name,
                    confidence=pattern_config["confidence"],
                    context=context
                )
                
                results.append(result)
        
        # Add high-entropy detections if enabled
        if include_high_entropy:
            entropy_results = self.detect_high_entropy_strings(content)
            results.extend(entropy_results)
        
        # Remove duplicates and sort by severity
        results = self._deduplicate_results(results)
        results.sort(key=lambda x: (x.severity.value, x.confidence), reverse=True)
        
        return results
    
    def _deduplicate_results(self, results: List[DetectionResult]) -> List[DetectionResult]:
        """Remove duplicate detection results."""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a key based on position and text
            key = (result.start_pos, result.end_pos, result.matched_text)
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def sanitize_content(self, content: str, detections: List[DetectionResult]) -> str:
        """Sanitize content by replacing detected sensitive data.
        
        Args:
            content: Content to sanitize
            detections: Detection results to sanitize
            
        Returns:
            Sanitized content
        """
        sanitized = content
        
        # Sort detections by position (reverse order to avoid offset issues)
        sorted_detections = sorted(detections, key=lambda x: x.start_pos, reverse=True)
        
        for detection in sorted_detections:
            # Create replacement based on data type
            replacement = self._create_replacement(detection)
            
            # Replace the sensitive data
            sanitized = (
                sanitized[:detection.start_pos] + 
                replacement + 
                sanitized[detection.end_pos:]
            )
        
        return sanitized
    
    def _create_replacement(self, detection: DetectionResult) -> str:
        """Create appropriate replacement for detected sensitive data."""
        data_type = detection.data_type
        
        replacements = {
            DataType.API_KEY: "[API_KEY_REDACTED]",
            DataType.PASSWORD: "[PASSWORD_REDACTED]",
            DataType.TOKEN: "[TOKEN_REDACTED]",
            DataType.SSH_KEY: "[SSH_KEY_REDACTED]",
            DataType.EMAIL: "[EMAIL_REDACTED]",
            DataType.CREDIT_CARD: "[CREDIT_CARD_REDACTED]",
            DataType.PHONE: "[PHONE_REDACTED]",
            DataType.SSN: "[SSN_REDACTED]",
            DataType.SECRET_KEY: "[SECRET_KEY_REDACTED]",
            DataType.CERTIFICATE: "[CERTIFICATE_REDACTED]",
            DataType.HIGH_ENTROPY: "[HIGH_ENTROPY_REDACTED]",
        }
        
        return replacements.get(data_type, "[SENSITIVE_DATA_REDACTED]")
    
    def get_summary(self, detections: List[DetectionResult]) -> Dict[str, Any]:
        """Get summary of detection results.
        
        Args:
            detections: Detection results to summarize
            
        Returns:
            Summary statistics
        """
        summary = {
            "total_detections": len(detections),
            "by_severity": {},
            "by_data_type": {},
            "high_confidence": [d for d in detections if d.confidence >= 0.8],
            "critical_issues": [d for d in detections if d.severity == SeverityLevel.CRITICAL],
        }
        
        # Count by severity
        for severity in SeverityLevel:
            summary["by_severity"][severity.value] = len([
                d for d in detections if d.severity == severity
            ])
        
        # Count by data type
        for data_type in DataType:
            summary["by_data_type"][data_type.value] = len([
                d for d in detections if d.data_type == data_type
            ])
        
        return summary
    
    def print_detections(self, detections: List[DetectionResult]) -> None:
        """Print detection results in a formatted way."""
        if not detections:
            self.console.print("[green]✓[/green] No sensitive data detected")
            return
        
        summary = self.get_summary(detections)
        
        self.console.print(f"\n[bold red]⚠️  Sensitive Data Detected[/bold red]")
        self.console.print(f"Total detections: [bold]{summary['total_detections']}[/bold]")
        
        # Show critical issues first
        critical = summary["critical_issues"]
        if critical:
            self.console.print(f"\n[bold red]🚨 Critical Issues ({len(critical)}):[/bold red]")
            for detection in critical[:5]:  # Show first 5
                self.console.print(f"  • {detection.data_type.value.upper()}: {detection.matched_text[:50]}...")
        
        # Show summary by severity
        self.console.print(f"\n[bold]By Severity:[/bold]")
        for severity, count in summary["by_severity"].items():
            if count > 0:
                color = {"critical": "red", "high": "yellow", "medium": "orange", "low": "blue"}[severity]
                self.console.print(f"  • {severity.capitalize()}: [{color}]{count}[/{color}]")
        
        # Show summary by data type
        self.console.print(f"\n[bold]By Data Type:[/bold]")
        for data_type, count in summary["by_data_type"].items():
            if count > 0:
                self.console.print(f"  • {data_type.replace('_', ' ').title()}: {count}")


# Global instance for easy access
content_filter = ContentFilter()
