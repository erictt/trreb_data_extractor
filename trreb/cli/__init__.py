"""
Command-line interface package for TRREB data extractor.
"""

# Import commands for easier access at the package level
from trreb.cli.commands import (
    fetch,
    convert,
    normalize,
    economy,
)

__all__ = [
    "fetch",
    "convert",
    "normalize",
    "economy",
]
