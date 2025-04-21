"""
Data processor package for TRREB data.
This module handles processing, normalization, and validation of the extracted CSV data.
"""

from .normalization import normalize_dataset
from .validation import generate_validation_report

__all__ = [
    "normalize_dataset",
    "generate_validation_report",
]
