"""
Logging configuration for TRREB data extractor.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str, 
    log_file: Optional[Path] = None, 
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    
    Args:
        name: Name of the logger
        log_file: Path to log file (if None, only console logging is used)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logger and set level
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Default logger for the package
logger = setup_logger('trreb')
