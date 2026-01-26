"""
Output Validators
Validate LLM-generated output before returning to user.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from ..base import GuardrailValidator, ValidationResult
from ..config import GuardrailsConfig

logger = logging.getLogger(__name__)


class CitationValidator(GuardrailValidator):
    """Validate citation format and quality."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(name="citation_validator", enabled=config.enable_citation_validation)
        self.min_citation_count = config.min_citation_count

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check citation format and count."""
        if not self.enabled:
            return ValidationResult.success(self.name, "Citation validation disabled")

        # Find all citations [1], [2], etc.
        citations = re.findall(r'\[(\d+)\]', text)

        if not citations:
            if self.min_citation_count > 0:
                return ValidationResult.error(
                    self.name,
                    f"No citations found (minimum required: {self.min_citation_count})",
                    metadata={"citation_count": 0},
                )
            return ValidationResult.warning(
                self.name,
                "No citations found in answer",
                metadata={"citation_count": 0},
            )

        # Convert to integers
        citation_nums = [int(c) for c in citations]
        unique_citations = len(set(citation_nums))

        # Check if citations start from 1
        if min(citation_nums) != 1:
            return ValidationResult.warning(
                self.name,
                f"Citations should start from [1], found minimum: [{min(citation_nums)}]",
                metadata={"min_citation": min(citation_nums)},
            )

        # Check if citations are sequential
        max_citation = max(citation_nums)
        expected = set(range(1, max_citation + 1))
        actual = set(citation_nums)
        missing = expected - actual

        if missing:
            return ValidationResult.warning(
                self.name,
                f"Non-sequential citations - missing: {sorted(missing)}",
                metadata={"missing_citations": sorted(missing)},
            )

        # Check minimum citation count
        if unique_citations < self.min_citation_count:
            return ValidationResult.warning(
                self.name,
                f"Low citation count: {unique_citations} (minimum: {self.min_citation_count})",
                metadata={"citation_count": unique_citations},
            )

        return ValidationResult.success(
            self.name,
            f"Citations valid: {unique_citations} unique sources",
            metadata={"citation_count": unique_citations},
        )


class HallucinationDetector(GuardrailValidator):
    """Detect hallucination markers in output."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(
            name="hallucination_detector", enabled=config.enable_hallucination_detection
        )
        self.patterns = config.hallucination_markers

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check for hallucination markers."""
        if not self.enabled:
            return ValidationResult.success(self.name, "Hallucination detection disabled")

        found_markers = []
        for pattern in self.patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_markers.extend(matches)

        if found_markers:
            logger.warning("Hallucination markers found: %s", found_markers)
            return ValidationResult.error(
                self.name,
                f"Potential hallucination markers found: {', '.join(set(found_markers)[:3])}",
                metadata={"markers": list(set(found_markers))},
            )

        return ValidationResult.success(self.name, "No hallucination markers detected")


class LengthValidator(GuardrailValidator):
    """Validate answer length."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(name="length_validator", enabled=config.enable_length_validation)
        self.min_sentences = config.min_answer_sentences
        self.max_sentences = config.max_answer_sentences
        self.max_length = config.max_answer_length

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check answer length constraints."""
        if not self.enabled:
            return ValidationResult.success(self.name, "Length validation disabled")

        # Count sentences (simple split on punctuation)
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        # Check character length
        char_length = len(text)

        issues = []

        if sentence_count < self.min_sentences:
            issues.append(
                f"Too short: {sentence_count} sentences (minimum: {self.min_sentences})"
            )

        if sentence_count > self.max_sentences:
            issues.append(
                f"Too long: {sentence_count} sentences (maximum: {self.max_sentences})"
            )

        if char_length > self.max_length:
            issues.append(
                f"Exceeds max length: {char_length} chars (maximum: {self.max_length})"
            )

        if issues:
            return ValidationResult.warning(
                self.name,
                "; ".join(issues),
                metadata={
                    "sentence_count": sentence_count,
                    "char_length": char_length,
                },
            )

        return ValidationResult.success(
            self.name,
            f"Length appropriate: {sentence_count} sentences, {char_length} chars",
            metadata={"sentence_count": sentence_count, "char_length": char_length},
        )


class HarmfulContentDetector(GuardrailValidator):
    """Detect harmful content in output."""

    def __init__(self, config: GuardrailsConfig):
        super().__init__(
            name="harmful_content_detector",
            enabled=config.enable_harmful_content_detection,
        )

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """Check for harmful content."""
        if not self.enabled:
            return ValidationResult.success(self.name, "Harmful content detection disabled")

        text_lower = text.lower()

        # Harmful content patterns (simplified)
        harmful_patterns = [
            "how to make a bomb",
            "how to hack",
            "commit suicide",
            "harm yourself",
            "violent content",
        ]

        for pattern in harmful_patterns:
            if pattern in text_lower:
                logger.error("Harmful content detected: %s", pattern)
                return ValidationResult.critical(
                    self.name,
                    f"Harmful content detected: '{pattern}'",
                    metadata={"pattern": pattern},
                )

        return ValidationResult.success(self.name, "No harmful content detected")


class OutputValidator:
    """Composite validator for all output checks."""

    def __init__(self, config: Optional[GuardrailsConfig] = None):
        """Initialize with validators."""
        if config is None:
            from ..config import load_guardrails_config
            config = load_guardrails_config()

        self.config = config
        self.validators = [
            CitationValidator(config),
            HallucinationDetector(config),
            LengthValidator(config),
            HarmfulContentDetector(config),
        ]

    def validate(self, text: str, metadata: Optional[dict] = None) -> tuple[bool, list[ValidationResult]]:
        """
        Run all output validators.

        Args:
            text: Output text to validate
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