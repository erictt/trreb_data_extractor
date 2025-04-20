"""
Facade module providing simplified high-level operations for TRREB data fetching.

This module provides a clean, simple interface to the more complex underlying components.
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from trreb.config import START_YEAR
from trreb.utils.logging import logger
from trreb.services.fetcher.downloader import TrrebDownloader
from trreb.services.fetcher.extractor import PageExtractor
from trreb.services.fetcher.report import ExtractionReport


def download_reports(start_year: Optional[int] = None) -> List[Path]:
    """
    Download all available TRREB market reports.
    
    Args:
        start_year: First year to download (default: config.START_YEAR)
        
    Returns:
        List of paths to downloaded files
    """
    downloader = TrrebDownloader()
    
    if start_year:
        logger.info(f"Downloading reports starting from year {start_year}")
        return downloader.download_all(start_year)
    
    logger.info(f"Downloading reports using default start year {START_YEAR}")
    return downloader.download_all()


def extract_page_from_pdf(pdf_path: Path, overwrite: bool = False) -> Dict[str, bool]:
    """
    Extract ALL HOME TYPES and DETACHED pages from a specific PDF.
    
    Args:
        pdf_path: Path to the PDF file
        overwrite: Whether to overwrite existing output files
        
    Returns:
        Dictionary with extraction results for each property type
    """
    extractor = PageExtractor()
    return extractor.extract_pdf_pages(pdf_path, overwrite)


def extract_all_pdfs(overwrite: bool = False) -> pd.DataFrame:
    """
    Extract pages from all PDFs in the default directory.
    
    Args:
        overwrite: Whether to overwrite existing output files
        
    Returns:
        DataFrame summarizing the extraction results
    """
    report_generator = ExtractionReport()
    return report_generator.generate_report(overwrite)


def fetch_and_extract_all(start_year: Optional[int] = None, overwrite: bool = False) -> pd.DataFrame:
    """
    Download all reports and extract the relevant pages.
    
    Args:
        start_year: First year to download (default: config.START_YEAR)
        overwrite: Whether to overwrite existing files
        
    Returns:
        DataFrame summarizing the extraction results
    """
    # First download all PDF files
    logger.info("Starting download and extraction process")
    download_reports(start_year)
    
    # Then extract pages from all PDFs
    logger.info("Starting page extraction.")
    return extract_all_pdfs(overwrite)
