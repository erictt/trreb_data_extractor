"""
TRREB Data Extractor package.

This package provides tools for downloading, extracting, and processing
Toronto Real Estate Board (TRREB) market reports.
"""

# Re-export services directly from the package root for backwards compatibility
from trreb.services.csv_converter import get_table_extractor, process_pdf
from trreb.services.data_processor import normalize_dataset, generate_validation_report
from trreb.services.fetcher import (
    download_reports,
    extract_page_from_pdf,
    extract_all_pdfs,
    fetch_and_extract_all,
)
from trreb.services.economic import (
    load_economic_data,
    create_master_economic_dataset,
    integrate_economic_data,
)

__all__ = [
    # CSV converter
    "get_table_extractor",
    "process_pdf",
    # Data processor
    "normalize_dataset",
    "generate_validation_report",
    # Downloader & PDF extractor
    "download_reports",
    "extract_page_from_pdf",
    "extract_all_pdfs",
    "fetch_and_extract_all",
    # Economic
    "load_economic_data",
    "create_master_economic_dataset",
    "integrate_economic_data",
]
