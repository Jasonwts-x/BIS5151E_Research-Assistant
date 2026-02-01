"""
Logging Configuration.

Centralized logging setup for all services.

This module provides a unified logging configuration that:
    - Formats logs consistently across services
    - Supports both console and file output
    - Suppresses noisy third-party loggers
    - Includes service name in log messages
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    service_name: str = "research-assistant",
):
    """
    Configure logging for the application.
    
    Sets up a root logger with consistent formatting across all services.
    Automatically suppresses verbose output from third-party libraries.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging output
        service_name: Service name for log formatting (appears in every log line)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter with service name
    formatter = logging.Formatter(
        f"%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info("Logging configured: level=%s", level)