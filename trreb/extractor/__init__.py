"""
Extractor package for TRREB data.
"""

from pathlib import Path
from typing import Optional

from trreb.config import EXTRACTION_CUTOFF_DATE
from trreb.extractor.base import BaseExtractor
from trreb.extractor.page_extractor import PageExtractor, extract_all_pages, extract_specific_pdf
from trreb.extractor.post_2020 import Post2020Extractor
from trreb.extractor.pre_2020 import Pre2020Extractor
from trreb.utils.logging import logger

__all__ = [
    "get_extractor",
    "PageExtractor",
    "extract_all_pages",
    "extract_specific_pdf",
    "process_pdf",
]


def get_extractor(date_str: str, property_type: str) -> BaseExtractor:
    """
    Factory function to get the appropriate extractor based on the date.
    
    Args:
        date_str: Date string in YYYY-MM format
        property_type: Property type (all_home_types or detached)
        
    Returns:
        Appropriate extractor instance
    """
    if date_str < EXTRACTION_CUTOFF_DATE:
        logger.info(f"Using Pre2020Extractor for {date_str}")
        return Pre2020Extractor(property_type)
    else:
        logger.info(f"Using Post2020Extractor for {date_str}")
        return Post2020Extractor(property_type)


def process_pdf(pdf_path: Path, output_path: Path, date_str: str, property_type: str) -> bool:
    """
    Process a single PDF using the appropriate extractor.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path to save the CSV output
        date_str: Date string in YYYY-MM format
        property_type: Property type (all_home_types or detached)
        
    Returns:
        True if processing was successful, False otherwise
    """
    extractor = get_extractor(date_str, property_type)
    success, _ = extractor.process_pdf(pdf_path, output_path)
    return success
