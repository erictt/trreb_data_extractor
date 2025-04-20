"""
Logging configuration for TRREB data extractor using loguru.
"""

import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any

from loguru import logger

# Remove the default handler
logger.remove()

# Add a default console handler with INFO level
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

def setup_logger(
    name: str, 
    log_file: Optional[Path] = None, 
    level: Union[str, int] = "INFO"
) -> logger.__class__:
    """
    Set up a loguru logger with console and optional file handlers.
    
    Args:
        name: Name of the logger (used in the format string)
        log_file: Path to log file (if None, only console logging is used)
        level: Logging level as string or int
        
    Returns:
        Configured logger instance
    """
    # Create a context-specific logger
    context_logger = logger.bind(name=name)
    
    # Ensure the level is correctly handled
    if isinstance(level, int):
        # Convert Python's logging levels to loguru levels
        level_map = {
            50: "CRITICAL",
            40: "ERROR",
            30: "WARNING",
            20: "INFO",
            10: "DEBUG",
            0: "TRACE"
        }
        level = level_map.get(level, "INFO")
    
    # Remove any previous handlers and add a new console handler with the specified level
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level
    )
    
    # Add file handler if log_file is provided
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[name]}:{function}:{line} - {message}",
            level=level,
            rotation="10 MB"  # Rotate files when they reach 10MB
        )
    
    # Only log a message for testing if log level allows it
    if level == "DEBUG":
        context_logger.debug("Logger debug test")
    if level in ["DEBUG", "INFO"]:
        context_logger.info("Logger initialized successfully")
    
    return context_logger

# Default logger for the package
logger = setup_logger('trreb')
