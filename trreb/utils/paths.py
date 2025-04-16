"""
Path handling utilities for TRREB data extractor.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    Extract the date from the filename if possible.
    
    Args:
        filename: Filename to parse
        
    Returns:
        String date in YYYY-MM format or None if date can't be extracted
    """
    # Handle the common TRREB naming format: mwYYMM.pdf
    mw_pattern = r"mw(\d{2})(\d{2})\.pdf"
    match = re.match(mw_pattern, filename.lower())
    if match:
        year, month = match.groups()
        # Adjust for 2-digit year format
        if 0 <= int(year) <= 99:
            if int(year) <= 25:  # Assuming current reports up to 2025
                year = f"20{year}"
            else:
                year = f"19{year}"
        return f"{year}-{month}"

    # Try other common patterns
    date_patterns = [
        r"(\d{4})[-_]?(\d{1,2})",  # YYYY-MM or YYYY_MM
        r"(\w+)[-_]?(\d{4})",  # Month-YYYY or Month_YYYY
    ]

    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                if groups[0].isdigit() and groups[1].isdigit():
                    # YYYY-MM format
                    return f"{groups[0]}-{groups[1].zfill(2)}"
                else:
                    # Month-YYYY format
                    month_str = groups[0]
                    year_str = groups[1]
                    try:
                        month_num = datetime.strptime(month_str[:3], "%b").month
                        return f"{year_str}-{str(month_num).zfill(2)}"
                    except ValueError:
                        pass

    # If no date found in filename, return None
    return None


def get_output_paths(date_str: str, property_type: str) -> Tuple[Path, Path]:
    """
    Get the output paths for the extracted page and processed CSV.
    
    Args:
        date_str: Date string in YYYY-MM format
        property_type: Property type (all_home_types or detached)
        
    Returns:
        Tuple of (extracted_path, processed_path)
    """
    from trreb.config import (
        ALL_HOMES_EXTRACTED_DIR, DETACHED_EXTRACTED_DIR,
        ALL_HOMES_PROCESSED_DIR, DETACHED_PROCESSED_DIR
    )
    
    if property_type == "all_home_types":
        extracted_path = ALL_HOMES_EXTRACTED_DIR / f"{date_str}.pdf"
        processed_path = ALL_HOMES_PROCESSED_DIR / f"{date_str}.csv"
    elif property_type == "detached":
        extracted_path = DETACHED_EXTRACTED_DIR / f"{date_str}.pdf"
        processed_path = DETACHED_PROCESSED_DIR / f"{date_str}.csv"
    else:
        raise ValueError(f"Unknown property type: {property_type}")
        
    return extracted_path, processed_path


def get_all_pdf_paths() -> list:
    """
    Get all PDF paths in the PDF directory.
    
    Returns:
        List of PDF file paths
    """
    from trreb.config import PDF_DIR
    return sorted([PDF_DIR / f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])


def get_all_extracted_paths(property_type: str) -> list:
    """
    Get all extracted PDF paths for a specific property type.
    
    Args:
        property_type: Property type (all_home_types or detached)
        
    Returns:
        List of extracted PDF file paths
    """
    from trreb.config import ALL_HOMES_EXTRACTED_DIR, DETACHED_EXTRACTED_DIR
    
    if property_type == "all_home_types":
        extracted_dir = ALL_HOMES_EXTRACTED_DIR
    elif property_type == "detached":
        extracted_dir = DETACHED_EXTRACTED_DIR
    else:
        raise ValueError(f"Unknown property type: {property_type}")
        
    return sorted([
        extracted_dir / f for f in os.listdir(extracted_dir) 
        if f.lower().endswith(".pdf")
    ])
