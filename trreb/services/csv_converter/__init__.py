"""
CSV converter package for TRREB data.
This module handles the conversion of extracted PDF pages into CSV format.
"""

from pathlib import Path
from typing import Optional

from trreb.config import EXTRACTION_CUTOFF_DATE
from trreb.services.csv_converter.base import TableExtractor
from trreb.services.csv_converter.post_2020 import Post2020TableExtractor
from trreb.services.csv_converter.pre_2020 import Pre2020TableExtractor
from trreb.utils.logging import logger

__all__ = [
    "get_table_extractor",
    "process_pdf",
]


def get_table_extractor(date_str: str, property_type: str) -> TableExtractor:
    """
    Factory function to get the appropriate table extractor based on the date.
    
    Args:
        date_str: Date string in YYYY-MM format
        property_type: Property type (all_home_types or detached)
        
    Returns:
        Appropriate extractor instance
    """
    if date_str < EXTRACTION_CUTOFF_DATE:
        logger.info(f"Using Pre2020TableExtractor for {date_str}")
        return Pre2020TableExtractor(property_type)
    else:
        logger.info(f"Using Post2020TableExtractor for {date_str}")
        return Post2020TableExtractor(property_type)


def process_pdf(pdf_path: Path, output_path: Path, date_str: str, property_type: str, overwrite: bool = False) -> bool:
    """
    Process a single PDF using the appropriate extractor to convert to CSV.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path to save the CSV output
        date_str: Date string in YYYY-MM format
        property_type: Property type (all_home_types or detached)
        overwrite: Whether to overwrite existing output file
        
    Returns:
        True if processing was successful, False otherwise
    """
    extractor = get_table_extractor(date_str, property_type)
    success, _ = extractor.process_pdf(pdf_path, output_path, overwrite)
    return success
