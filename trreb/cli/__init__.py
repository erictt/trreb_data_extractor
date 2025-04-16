"""
Command-line interface package for TRREB data extractor.
"""

from trreb.cli.commands import (
    download,
    extract_pages,
    process,
    run_pipeline,
)

__all__ = [
    "download",
    "extract_pages",
    "process",
    "run_pipeline",
]
