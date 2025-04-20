"""
TRREB Data Fetcher package for downloading and extracting Toronto real estate market data.

This package provides functionality to:
1. Download PDF market reports from the TRREB website
2. Identify specific page types (ALL HOME TYPES, DETACHED, etc.)
3. Extract and save relevant pages as separate PDFs
4. Generate summary reports of the extraction process

The package is structured with separation of concerns:
- downloader.py: Handles all PDF download operations
- identifier.py: Identifies page types in PDFs
- extractor.py: Extracts specific pages from PDFs
- report.py: Generates summary information
- facade.py: Provides simplified high-level operations

Public exports for simplified usage:
"""

# Import the high-level operations for direct access
from trreb.services.fetcher.facade import (
    download_reports,
    extract_page_from_pdf, 
    extract_all_pdfs,
    fetch_and_extract_all
)

# Also expose component classes for advanced usage
from trreb.services.fetcher.downloader import TrrebDownloader
from trreb.services.fetcher.identifier import PageIdentifier
from trreb.services.fetcher.extractor import PageExtractor
from trreb.services.fetcher.report import ExtractionReport

__all__ = [
    # High-level operations
    'download_reports',
    'extract_page_from_pdf',
    'extract_all_pdfs',
    'fetch_and_extract_all',
    
    # Component classes
    'TrrebDownloader',
    'PageIdentifier',
    'PageExtractor',
    'ExtractionReport'
]
