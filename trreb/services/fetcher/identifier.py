"""
Module for identifying specific page types in TRREB market reports.
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional

import PyPDF2

from trreb.config import ALL_HOMES_EXTRACTED_DIR
from trreb.utils.logging import logger


class PageIdentifier:
    """
    Class for identifying specific page types in TRREB market report PDFs.
    
    Identifies pages containing:
    - ALL HOME TYPES data
    - DETACHED homes data
    
    Uses pattern matching against page text to find the correct pages.
    """
    
    def __init__(self):
        """Initialize the page identifier with search patterns."""
        # Patterns to search for ALL HOME TYPES pages
        self.all_homes_patterns = [
            r"(ALL HOME TYPES,|SUMMARY OF EXISTING HOME TRANSACTIONS All Home Types)",
            r"SUMMARY OF EXISTING HOME TRANSACTIONS ALL TRREB AREAS",
            r"SUMMARY OF EXISTING HOME TRANSACTIONS ALL TREB AREAS",
        ]
        
        # Patterns to search for DETACHED pages
        self.detached_patterns = [
            r"(DETACHED,|SUMMARY OF EXISTING HOME TRANSACTIONS Detached)",
            r"SUMMARY OF EXISTING HOME TRANSACTIONS DETACHED",
            r"DETACHED, [A-Z]+ \d{4}",
            r"SUMMARY OF SALES AND AVERAGE PRICE BY MAJOR HOME TYPE, DETACHED",
        ]
    
    def identify_pages(self, pdf_path: Path, save_debug_info: bool = True) -> Dict[str, Optional[int]]:
        """
        Identify the page numbers for "ALL HOME TYPES" and "DETACHED" sections.
        
        Args:
            pdf_path: Path to the PDF file
            save_debug_info: Whether to save debug info to a file
            
        Returns:
            Dictionary with keys 'all_home_types' and 'detached' containing the page numbers
        """
        result = {"all_home_types": None, "detached": None}
        
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Log all page titles for debugging
                page_titles = []
                
                # Iterate through pages to find matching sections (limit to first 30 pages)
                for page_num in range(min(num_pages, 30)):
                    try:
                        page_text = pdf_reader.pages[page_num].extract_text()
                        
                        # Store first few lines of each page for logging
                        first_lines = " | ".join(page_text.split("\n")[:3])
                        page_titles.append(f"Page {page_num + 1}: {first_lines[:300]}")
                        
                        # Check for ALL HOME TYPES patterns
                        if result["all_home_types"] is None:
                            for pattern in self.all_homes_patterns:
                                if re.search(pattern, page_text, re.IGNORECASE):
                                    if (
                                        "ALL TRREB AREAS" in page_text
                                        or "ALL TREB AREAS" in page_text
                                    ):
                                        result["all_home_types"] = page_num
                                        break
                        
                        # Check for DETACHED patterns
                        if result["detached"] is None:
                            for pattern in self.detached_patterns:
                                if re.search(pattern, page_text, re.IGNORECASE):
                                    if (
                                        "ALL TRREB AREAS" in page_text
                                        or "ALL TREB AREAS" in page_text
                                    ):
                                        result["detached"] = page_num
                                        break
                        
                        # Exit early if found both page types
                        if result["all_home_types"] is not None and result["detached"] is not None:
                            break
                    except Exception as e:
                        logger.error(f"Error extracting text from page {page_num}: {e}")
                        continue
                
                # Fall back to table-based identification for older reports
                if result["detached"] is None:
                    self._fallback_detached_identification(pdf_reader, result)
                
                # Write page titles to file for debugging if needed
                if save_debug_info:
                    self._save_debug_info(pdf_path, page_titles)
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
        
        return result
    
    def _fallback_detached_identification(self, pdf_reader: PyPDF2.PdfReader, result: Dict[str, Optional[int]]) -> None:
        """
        Use alternative methods to identify detached pages if standard patterns fail.
        
        Args:
            pdf_reader: The PDF reader object
            result: Result dictionary to update
        """
        num_pages = len(pdf_reader.pages)
        
        for page_num in range(min(num_pages, 30)):
            try:
                page_text = pdf_reader.pages[page_num].extract_text()
                
                # Check if it's a sales by property type page
                if (
                    "DETACHED" in page_text
                    and "SALES" in page_text.upper()
                    and "AVERAGE PRICE" in page_text.upper()
                ):
                    # Look for distinctive patterns that indicate this is the main detached page
                    if (
                        "ALL TREB AREAS" in page_text
                        or "ALL TRREB AREAS" in page_text
                    ):
                        result["detached"] = page_num
                        break
                
                # For older reports (2016-2019), look for pages with "Detached" in the title
                if (
                    "SUMMARY OF EXISTING HOME TRANSACTIONS" in page_text.upper()
                    and "DETACHED" in page_text.upper()
                ):
                    result["detached"] = page_num
                    break
            except Exception as e:
                logger.error(f"Error in fallback extraction from page {page_num}: {e}")
                continue
    
    def _save_debug_info(self, pdf_path: Path, page_titles: list) -> None:
        """
        Save page titles to a debug file for analysis.
        
        Args:
            pdf_path: Path to the PDF file
            page_titles: List of page title strings
        """
        debug_file = ALL_HOMES_EXTRACTED_DIR.parent / "page_titles.txt"
        
        # Create directory if it doesn't exist
        os.makedirs(ALL_HOMES_EXTRACTED_DIR.parent, exist_ok=True)
        
        with open(debug_file, "a") as f:
            f.write(f"\n\n--- {os.path.basename(pdf_path)} ---\n")
            f.write("\n".join(page_titles))
