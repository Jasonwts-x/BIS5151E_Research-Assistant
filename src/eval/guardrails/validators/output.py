"""
Output Validators
Validate LLM-generated output before returning to user.
"""
from __future__ import annotations
 
import logging
import re
from typing import Optional
 
from ..base import GuardrailValidator, ValidationResult, ValidationLevel
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
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.INFO,
                message="Citation validation disabled",
                metadata=metadata or {}
            )
 
        # Find all citations [1], [2], etc.
        citations = re.findall(r'\[(\d+)\]', text)
 
        if not citations:
            if self.min_citation_count > 0:
                return ValidationResult(
                    validator_name=self.name,
                    passed=False,
                    level=ValidationLevel.ERROR,
                    message=f"No citations found (minimum required: {self.min_citation_count})",
                    metadata={"citation_count": 0}
                )
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.WARNING,
                message="No citations found in answer",
                metadata={"citation_count": 0}
            )
 
        # Convert to integers
        citation_nums = [int(c) for c in citations]
        unique_citations = len(set(citation_nums))
 
        # Check if citations start from 1
        if min(citation_nums) != 1:
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.WARNING,
                message=f"Citations should start from [1], found minimum: [{min(citation_nums)}]",
                metadata={"min_citation": min(citation_nums)}
            )
 
        # Check if citations are sequential
        max_citation = max(citation_nums)
        expected = set(range(1, max_citation + 1))
        actual = set(citation_nums)
        missing = expected - actual
 
        if missing:
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.WARNING,
                message=f"Non-sequential citations - missing: {sorted(missing)}",
                metadata={"missing_citations": sorted(missing)}
            )
 
        # Check minimum citation count
        if unique_citations < self.min_citation_count:
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.WARNING,
                message=f"Low citation count: {unique_citations} (minimum: {self.min_citation_count})",
                metadata={"citation_count": unique_citations}
            )
 
        return ValidationResult(
            validator_name=self.name,
            passed=True,
            level=ValidationLevel.INFO,
            message=f"Citations valid: {unique_citations} unique sources",
            metadata={"citation_count": unique_citations}
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
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.INFO,
                message="Hallucination detection disabled",
                metadata=metadata or {}
            )
 
        found_markers = []
        for pattern in self.patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_markers.extend(matches)
 
        if found_markers:
            logger.warning("Hallucination markers found: %s", found_markers)
            return ValidationResult(
                validator_name=self.name,
                passed=False,
                level=ValidationLevel.ERROR,
                message=f"Potential hallucination markers found: {', '.join(set(found_markers)[:3])}",
                metadata={"markers": list(set(found_markers))}
            )
 
        return ValidationResult(
            validator_name=self.name,
            passed=True,
            level=ValidationLevel.INFO,
            message="No hallucination markers detected",
            metadata=metadata or {}
        )
 
 
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
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.INFO,
                message="Length validation disabled",
                metadata=metadata or {}
            )
 
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
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.WARNING,
                message="; ".join(issues),
                metadata={
                    "sentence_count": sentence_count,
                    "char_length": char_length,
                }
            )
 
        return ValidationResult(
            validator_name=self.name,
            passed=True,
            level=ValidationLevel.INFO,
            message=f"Length appropriate: {sentence_count} sentences, {char_length} chars",
            metadata={"sentence_count": sentence_count, "char_length": char_length}
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
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                level=ValidationLevel.INFO,
                message="Harmful content detection disabled",
                metadata=metadata or {}
            )
 
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
                return ValidationResult(
                    validator_name=self.name,
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"Harmful content detected: '{pattern}'",
                    metadata={"pattern": pattern}
                )
 
        return ValidationResult(
            validator_name=self.name,
            passed=True,
            level=ValidationLevel.INFO,
            message="No harmful content detected",
            metadata=metadata or {}
        )
 
 
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
        passed = all(r.passed or r.level == ValidationLevel.WARNING for r in results)
 
        # In strict mode, warnings become errors
        if self.config.strict_mode:
            passed = all(r.passed for r in results)
 
        return passed, results
 
    def get_summary(self, results: list[ValidationResult]) -> dict:
        """Get summary of validation results."""
        return {
            "total_checks": len(results),
            "passed": sum(1 for r in results if r.passed),
            "warnings": sum(1 for r in results if r.level == ValidationLevel.WARNING),
            "errors": sum(1 for r in results if not r.passed and r.level == ValidationLevel.ERROR),
            "critical": sum(
                1 for r in results if r.level == ValidationLevel.CRITICAL and not r.passed
            ),
        }
 
    def _check_citation_format(self, text: str) -> ValidationResult:
        """
        Check that citations follow proper format [1], [2], etc.
    
        Args:
            text: Text to validate
        
        Returns:
            ValidationResult indicating if citations are properly formatted
        """
        import re
    
        # Find all potential citations
        citations = re.findall(r'\[(\d+)\]', text)
    
        if not citations:
            return ValidationResult(
                passed=True,
                message="No citations found (acceptable if no sources used)",
                severity="info"
            )
    
        # Check if citations are sequential starting from 1
        citation_nums = [int(c) for c in citations]
        unique_citations = sorted(set(citation_nums))
    
        # Should start at 1 and be sequential
        expected = list(range(1, len(unique_citations) + 1))
    
        if unique_citations != expected:
            return ValidationResult(
                passed=False,
                message=f"Citations not sequential. Found: {unique_citations}, expected: {expected}",
                severity="warning"
            )
    
        return ValidationResult(
            passed=True,
            message=f"Citations properly formatted ({len(unique_citations)} unique)",
            severity="info"
        )