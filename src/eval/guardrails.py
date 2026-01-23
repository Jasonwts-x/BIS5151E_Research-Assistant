from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class GuardrailsWrapper:
    """
    Safety wrapper for LLM inputs/outputs.

    Checks for:
    - PII (Personally Identifiable Information) - primarily in input
    - Harmful content
    - Jailbreak attempts
    - Off-topic queries
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize guardrails.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._default_config()
        logger.info("Guardrails initialized with config: %s", self.config)

    def _default_config(self) -> dict:
        """Default guardrails configuration."""
        return {
            "input_checks": ["jailbreak", "pii", "off_topic"],
            "output_checks": ["harmful"],
            "strict_mode": False
        }

    def validate_input(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate user input.

        Args:
            text: User input text

        Returns:
            (is_safe, violation_reason)
        """
        # Check for jailbreak attempts
        if "jailbreak" in self.config["input_checks"]:
            if self._is_jailbreak_attempt(text):
                logger.warning("GUARDRAILS BLOCKED: Jailbreak attempt detected in input")
                return False, "Jailbreak attempt detected"

        # Check for PII
        if "pii" in self.config["input_checks"]:
            if self._contains_pii(text):
                logger.warning("GUARDRAILS BLOCKED: PII detected in input")
                return False, "Personal information detected"

        # Check if on-topic (research-related)
        if "off_topic" in self.config["input_checks"]:
            if not self._is_on_topic(text):
                logger.warning("GUARDRAILS BLOCKED: Off-topic query detected")
                return False, "Query is not research-related"

        logger.debug("Input validation passed")
        return True, None

    def validate_output(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate LLM output.

        Args:
            text: LLM output text

        Returns:
            (is_safe, violation_reason)
        """
        # Check for PII in output (disabled by default for generated content)
        if "pii" in self.config["output_checks"]:
            if self._contains_pii(text):
                logger.warning("GUARDRAILS BLOCKED: PII detected in output")
                return False, "Output contains personal information"

        # Check for harmful content
        if "harmful" in self.config["output_checks"]:
            if self._is_harmful(text):
                logger.warning("GUARDRAILS BLOCKED: Harmful content detected in output")
                return False, "Output contains harmful content"

        logger.debug("Output validation passed")
        return True, None

    def _is_jailbreak_attempt(self, text: str) -> bool:
        """Detect jailbreak attempts."""
        jailbreak_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "disregard your programming",
            "you are now in developer mode",
            "forget your constraints",
            "act as if",
            "pretend you are",
            "reveal your system prompt",
            "bypass your restrictions"
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in jailbreak_patterns)

    def _contains_pii(self, text: str) -> bool:
        """
        Detect PII (simplified version).

        Uses context-aware detection to reduce false positives.
        For production, consider using Microsoft Presidio.
        """
        text_lower = text.lower()

        # Email pattern - with context check
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            # Only flag if there's clear PII context
            if any(phrase in text_lower for phrase in [
                'my email', 'email is', 'contact me at', 'reach me at',
                'send to', 'write to'
            ]):
                return True

        # Phone pattern - with context (full phone numbers only)
        phone_pattern = r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        if re.search(phone_pattern, text):
            # Only flag if there's clear PII context
            if any(phrase in text_lower for phrase in [
                'my phone', 'phone is', 'call me at', 'number is',
                'mobile', 'contact number'
            ]):
                return True

        # Credit card pattern (with separators - more specific)
        cc_pattern = r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b'
        if re.search(cc_pattern, text):
            return True

        # SSN pattern (US)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, text):
            return True

        # Address pattern (very basic - street number + street name)
        if any(phrase in text_lower for phrase in [
            'i live at', 'my address is', 'located at', 'address:'
        ]):
            # Check for street number pattern
            if re.search(r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b', text_lower):
                return True

        return False

    def _is_on_topic(self, text: str) -> bool:
        """
        Check if query is research-related.

        This is a simple keyword-based approach.
        For production, consider using semantic similarity with embeddings.
        """
        # Off-topic indicators
        off_topic_keywords = [
            "hack", "exploit", "crack", "pirate", "illegal",
            "buy", "sell", "price", "discount", "shopping",
            "dating", "relationship"
        ]

        text_lower = text.lower()

        # If query is very short, be more lenient
        if len(text.split()) < 5:
            return True

        # Check for off-topic keywords
        if any(keyword in text_lower for keyword in off_topic_keywords):
            # Allow if it's in academic context
            academic_context = [
                "research", "study", "analysis", "theory", "academic",
                "explain", "what is", "how does", "definition"
            ]
            if not any(ctx in text_lower for ctx in academic_context):
                return False

        return True

    def _is_harmful(self, text: str) -> bool:
        """
        Check for harmful content (simplified).

        For production, use content moderation APIs like OpenAI Moderation API.
        """
        harmful_patterns = [
            "violent", "violence", "kill", "murder", "harm",
            "illegal activity", "crime", "discriminatory", "racist",
            "hate speech", "explicit content", "offensive"
        ]

        text_lower = text.lower()

        # Count harmful pattern matches
        matches = sum(
            1 for pattern in harmful_patterns if pattern in text_lower)

        # Require multiple matches or very explicit single match
        if matches >= 2:
            return True

        # Check for very explicit single harmful terms
        explicit_harmful = ["kill", "murder", "racist", "hate speech"]
        if any(term in text_lower for term in explicit_harmful):
            return True

        return False