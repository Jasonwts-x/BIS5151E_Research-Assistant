"""
Base Guardrails Classes
Foundation for validation logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationLevel(Enum):
    """Severity level for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    level: ValidationLevel
    message: str
    validator_name: str
    metadata: Optional[dict] = None

    @classmethod
    def success(cls, validator_name: str, message: str = "Validation passed"):
        """Create success result."""
        return cls(
            passed=True,
            level=ValidationLevel.INFO,
            message=message,
            validator_name=validator_name,
        )

    @classmethod
    def warning(cls, validator_name: str, message: str, metadata: Optional[dict] = None):
        """Create warning result."""
        return cls(
            passed=True,  # Warnings don't fail validation
            level=ValidationLevel.WARNING,
            message=message,
            validator_name=validator_name,
            metadata=metadata,
        )

    @classmethod
    def error(cls, validator_name: str, message: str, metadata: Optional[dict] = None):
        """Create error result."""
        return cls(
            passed=False,
            level=ValidationLevel.ERROR,
            message=message,
            validator_name=validator_name,
            metadata=metadata,
        )

    @classmethod
    def critical(cls, validator_name: str, message: str, metadata: Optional[dict] = None):
        """Create critical error result."""
        return cls(
            passed=False,
            level=ValidationLevel.CRITICAL,
            message=message,
            validator_name=validator_name,
            metadata=metadata,
        )


class GuardrailValidator:
    """Base class for all guardrail validators."""

    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize validator.

        Args:
            name: Validator name
            enabled: Whether validator is enabled
        """
        self.name = name
        self.enabled = enabled

    def validate(self, text: str, metadata: Optional[dict] = None) -> ValidationResult:
        """
        Validate text.

        Args:
            text: Text to validate
            metadata: Optional metadata

        Returns:
            ValidationResult
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"