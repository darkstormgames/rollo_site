"""Logging configuration for VM Service."""
import logging
import sys
from typing import Dict, Any
from .config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    
    # Create formatter
    formatter = logging.Formatter(settings.log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    loggers_config = {
        "uvicorn": logging.INFO,
        "uvicorn.error": logging.INFO,
        "uvicorn.access": logging.INFO,
        "fastapi": logging.INFO,
        "sqlalchemy.engine": logging.WARNING,
        "vm_service": getattr(logging, settings.log_level.upper()),
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        if not logger.handlers:
            logger.addHandler(console_handler)
        logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(f"vm_service.{name}")