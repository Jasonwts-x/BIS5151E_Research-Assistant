"""
Input Validators
Validate user input before processing.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from ..base import GuardrailValidator, ValidationResult
from ..config import GuardrailsConfig

logger = logging.getLogger(__name__)


class JailbreakDetector(GuardrailValidator):
    """Detect jailbreak attempts in user input."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(name="jailbreak_detector", enabled=config.enable_jailbreak_detection)
        self.patterns = config.jailbreak_patterns

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check for jailbreak patterns."""
        if not self.enabled:
            return ValidationResult.success(self.name, "Jailbreak detection disabled")

        text_lower = text.lower()
        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                logger.warning("Jailbreak attempt detected: %s", pattern)
                return ValidationResult.critical(
                    self.name,
                    f"Potential jailbreak attempt detected: '{pattern}'",
                    metadata={"pattern": pattern},
                )

        return ValidationResult.success(self.name, "No jailbreak patterns detected")


class PIIDetector(GuardrailValidator):
    """Detect personally identifiable information in input."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(name="pii_detector", enabled=config.enable_pii_detection)

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check for PII."""
        if not self.enabled:
            return ValidationResult.success(self.name, "PII detection disabled")

        issues = []
        text_lower = text.lower()

        # Email detection with context
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            if any(phrase in text_lower for phrase in [
                'my email', 'email is', 'contact me at', 'reach me at'
            ]):
                issues.append("email address")

        # Phone number detection (full numbers only)
        phone_pattern = r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        if re.search(phone_pattern, text):
            if any(phrase in text_lower for phrase in [
                'my phone', 'call me', 'phone number', 'mobile', 'contact'
            ]):
                issues.append("phone number")

        # Credit card detection (simplified)
        cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        if re.search(cc_pattern, text):
            issues.append("credit card number")

        # SSN detection (US format)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, text):
            issues.append("social security number")

        if issues:
            logger.warning("PII detected: %s", issues)
            return ValidationResult.error(
                self.name,
                f"Personal information detected: {', '.join(issues)}",
                metadata={"pii_types": issues},
            )

        return ValidationResult.success(self.name, "No PII detected")


class TopicRelevanceChecker(GuardrailValidator):
    """Check if query is relevant to research topics."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(
            name="topic_relevance_checker", enabled=config.enable_off_topic_detection
        )

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check if query is research-related."""
        if not self.enabled:
            return ValidationResult.success(self.name, "Topic relevance checking disabled")

        # Very simple heuristic - can be improved with ML
        text_lower = text.lower()

        # Obvious off-topic patterns
        off_topic_patterns = [
            "write me a poem",
            "tell me a joke",
            "what's the weather",
            "play a game",
            "sing a song",
            "how are you",
            "what's your name",
        ]

        for pattern in off_topic_patterns:
            if pattern in text_lower:
                return ValidationResult.warning(
                    self.name,
                    f"Query might be off-topic for research assistant: '{pattern}'",
                    metadata={"pattern": pattern},
                )

        # Check for research-related keywords (permissive)
        research_keywords = [
            "research", "study", "paper", "explain", "what is", "how does",
            "analyze", "compare", "review", "summary", "theory", "method",
        ]

        if any(keyword in text_lower for keyword in research_keywords):
            return ValidationResult.success(
                self.name, "Query appears research-related"
            )

        # If no clear indicators, allow with warning
        if len(text.split()) < 3:
            return ValidationResult.warning(
                self.name,
                "Query is very short - might lack research context",
            )

        return ValidationResult.success(
            self.name, "Query appears acceptable (no off-topic indicators)"
        )


class InputValidator:
    """Composite validator for all input checks."""

    def __init__(self, config: Optional[GuardrailsConfig] = None):
        """Initialize with validators."""
        if config is None:
            from ..config import load_guardrails_config
            config = load_guardrails_config()

        self.config = config
        self.validators = [
            JailbreakDetector(config),
            PIIDetector(config),
            TopicRelevanceChecker(config),
        ]

    def validate(self, text: str, metadata: Optional[dict] = None) -> tuple[bool, list[ValidationResult]]:
        """
        Run all input validators.

        Args:
            text: Input text to validate
            metadata: Optional metadata

        Returns:
            (passed, results) - Tuple of overall pass/fail and list of results
        """
        results = []
        for validator in self.validators:
            if validator.enabled:
                result = validator.validate(text, metadata)
                results.append(result)

        # Check if any critical or error results exist
        passed = all(r.passed or r.level.value == "warning" for r in results)

        # In strict mode, warnings become errors
        if self.config.strict_mode:
            passed = all(r.passed for r in results)

        return passed, results

    def get_summary(self, results: list[ValidationResult]) -> dict:
        """Get summary of validation results."""
        return {
            "total_checks": len(results),
            "passed": sum(1 for r in results if r.passed),
            "warnings": sum(1 for r in results if r.level.value == "warning"),
            "errors": sum(1 for r in results if not r.passed),
            "critical": sum(
                1 for r in results if r.level.value == "critical" and not r.passed
            ),
        }