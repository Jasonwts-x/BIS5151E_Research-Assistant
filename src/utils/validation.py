"""
Configuration Validation.

Validate environment variables and configuration at startup.

This module provides validation functions to catch configuration
errors early, before services start processing requests.
"""
from __future__ import annotations

import logging
import os
from typing import List, Tuple

logger = logging.getLogger(__name__)


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate required environment variables.
    
    Checks that all required environment variables are set and
    validates their format where applicable (e.g., URLs).
    
    Returns:
        Tuple of (is_valid, errors) where:
            - is_valid: True if all validations pass
            - errors: List of error messages (empty if valid)
    """
    errors = []
    
    # Required variables
    required = [
        "WEAVIATE_URL",
        "OLLAMA_HOST",
    ]
    
    for var in required:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate URL formats
    weaviate_url = os.getenv("WEAVIATE_URL", "")
    if weaviate_url and not weaviate_url.startswith("http"):
        errors.append(f"Invalid WEAVIATE_URL: {weaviate_url} (must start with http:// or https://)")
    
    ollama_host = os.getenv("OLLAMA_HOST", "")
    if ollama_host and not ollama_host.startswith("http"):
        errors.append(f"Invalid OLLAMA_HOST: {ollama_host} (must start with http:// or https://)")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        for error in errors:
            logger.error(error)
    else:
        logger.info("Environment validation passed")
    
    return is_valid, errors