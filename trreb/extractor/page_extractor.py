"""
Module for extracting specific pages from TRREB PDF reports.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import PyPDF2

from trreb.config import (
    ALL_HOMES_EXTRACTED_DIR, 
    DETACHED_EXTRACTED_DIR,
    PDF_DIR
)
from trreb.utils.logging import logger
from trreb.utils.paths import extract_date_from_filename, get_output_paths


class PageExtractor:
    """Class for extracting specific pages from TRREB PDF reports."""
    
    def __init__(self) -> None:
        """Initialize the PageExtractor."""
        # Ensure output directories exist
        os.makedirs(ALL_HOMES_EXTRACTED_DIR, exist_ok=True)
        os.makedirs(DETACHED_EXTRACTED_DIR, exist_ok=True)
    
    def identify_page_types(self, pdf_path: Path) -> Dict[str, Optional[int]]:
        """
        Identify the page numbers for "ALL HOME TYPES" and "DETACHED" sections.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with keys 'all_home_types' and 'detached' containing the page numbers
        """
        result = {"all_home_types": None, "detached": None}
        
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Patterns to search for (expanded for more formats)
                all_homes_patterns = [
                    r"(ALL HOME TYPES,|SUMMARY OF EXISTING HOME TRANSACTIONS All Home Types)",
                    r"SUMMARY OF EXISTING HOME TRANSACTIONS ALL TRREB AREAS",
                    r"SUMMARY OF EXISTING HOME TRANSACTIONS ALL TREB AREAS",
                ]
                
                detached_patterns = [
                    r"(DETACHED,|SUMMARY OF EXISTING HOME TRANSACTIONS Detached)",
                    r"SUMMARY OF EXISTING HOME TRANSACTIONS DETACHED",
                    r"DETACHED, [A-Z]+ \d{4}",
                    r"SUMMARY OF SALES AND AVERAGE PRICE BY MAJOR HOME TYPE, DETACHED",
                ]
                
                # Log all page titles for debugging
                page_titles = []
                
                # Iterate through pages to find matching sections
                for page_num in range(min(num_pages, 30)):  # Limit to first 30 pages
                    try:
                        page_text = pdf_reader.pages[page_num].extract_text()
                        # Store first few lines of each page for logging
                        first_lines = " | ".join(page_text.split("\n")[:3])
                        page_titles.append(f"Page {page_num + 1}: {first_lines[:300]}")
                        
                        # Check for ALL HOME TYPES patterns
                        if result["all_home_types"] is None:
                            for pattern in all_homes_patterns:
                                if re.search(pattern, page_text, re.IGNORECASE):
                                    if (
                                        "ALL TRREB AREAS" in page_text
                                        or "ALL TREB AREAS" in page_text
                                    ):
                                        result["all_home_types"] = page_num
                                        break
                        
                        # Check for DETACHED patterns
                        if result["detached"] is None:
                            for pattern in detached_patterns:
                                if re.search(pattern, page_text, re.IGNORECASE):
                                    if (
                                        "ALL TRREB AREAS" in page_text
                                        or "ALL TREB AREAS" in page_text
                                    ):
                                        result["detached"] = page_num
                                        break
                    except Exception as e:
                        logger.error(f"Error extracting text from page {page_num}: {e}")
                        continue
                
                # Fall back to table-based identification for older reports
                if result["detached"] is None:
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
                
                # Write page titles to file for debugging if needed
                debug_file = ALL_HOMES_EXTRACTED_DIR.parent / "page_titles.txt"
                with open(debug_file, "a") as f:
                    f.write(f"\n\n--- {os.path.basename(pdf_path)} ---\n")
                    f.write("\n".join(page_titles))
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
        
        return result
    
    def extract_page_as_pdf(self, pdf_path: Path, page_num: Optional[int], output_path: Path) -> bool:
        """
        Extract a specific page as a new PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number to extract (0-indexed)
            output_path: Path to save the extracted page
            
        Returns:
            True if successful, False otherwise
        """
        if page_num is None:
            logger.warning(f"No page number specified for {pdf_path}")
            return False
        
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if page_num >= len(pdf_reader.pages):
                    logger.warning(f"Page {page_num} out of bounds for {pdf_path}")
                    return False
                
                pdf_writer = PyPDF2.PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, "wb") as output_file:
                    pdf_writer.write(output_file)
            
            logger.info(f"Extracted page {page_num} from {pdf_path} to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error extracting page {page_num} from {pdf_path}: {e}")
            return False
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, bool]:
        """
        Process a single PDF file to extract relevant pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with extraction results for each property type
        """
        result = {
            "all_home_types_extracted": False,
            "detached_extracted": False
        }
        
        # Get date from filename
        date_str = extract_date_from_filename(pdf_path.name)
        if not date_str:
            # Use original filename as fallback
            logger.warning(f"Could not extract date from {pdf_path.name}. Using filename as identifier.")
            date_str = pdf_path.stem
        
        logger.info(f"Processing {pdf_path.name} (Date: {date_str})...")
        
        # Identify page types
        page_info = self.identify_page_types(pdf_path)
        
        # Extract and save pages with unique filenames to type-specific folders
        if page_info["all_home_types"] is not None:
            all_homes_path = ALL_HOMES_EXTRACTED_DIR / f"{date_str}.pdf"
            result["all_home_types_extracted"] = self.extract_page_as_pdf(
                pdf_path, page_info["all_home_types"], all_homes_path
            )
            if result["all_home_types_extracted"]:
                logger.info(f"  ✓ ALL HOME TYPES page extracted to {all_homes_path.name}")
            else:
                logger.warning(f"  ✗ Failed to extract ALL HOME TYPES page")
        else:
            logger.warning(f"  ✗ ALL HOME TYPES page not found")
        
        if page_info["detached"] is not None:
            detached_path = DETACHED_EXTRACTED_DIR / f"{date_str}.pdf"
            result["detached_extracted"] = self.extract_page_as_pdf(
                pdf_path, page_info["detached"], detached_path
            )
            if result["detached_extracted"]:
                logger.info(f"  ✓ DETACHED page extracted to {detached_path.name}")
            else:
                logger.warning(f"  ✗ Failed to extract DETACHED page")
        else:
            logger.warning(f"  ✗ DETACHED page not found")
        
        return result
    
    def process_all_pdfs(self) -> pd.DataFrame:
        """
        Process all PDF files in the PDF directory.
        
        Returns:
            DataFrame summarizing the extraction results
        """
        results = []
        
        # Get all PDF files
        pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])
        
        for pdf_file in pdf_files:
            pdf_path = PDF_DIR / pdf_file
            
            # Get date from filename
            date_str = extract_date_from_filename(pdf_file)
            if not date_str:
                # Use original filename as fallback
                logger.warning(f"Could not extract date from {pdf_file}. Using filename as identifier.")
                date_str = os.path.splitext(pdf_file)[0]
            
            # Process the PDF
            result = self.process_pdf(pdf_path)
            
            # Add to results
            results.append({
                "filename": pdf_file,
                "date": date_str,
                "all_home_types_page": self.identify_page_types(pdf_path)["all_home_types"],
                "all_home_types_extracted": result["all_home_types_extracted"],
                "detached_page": self.identify_page_types(pdf_path)["detached"],
                "detached_extracted": result["detached_extracted"],
            })
        
        # Create a summary DataFrame
        summary_df = pd.DataFrame(results)
        summary_path = ALL_HOMES_EXTRACTED_DIR.parent / "extraction_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        
        logger.info(f"Extraction complete! Summary saved to {summary_path}")
        
        # Print statistics
        total_pdfs = len(results)
        successful_all_homes = sum(1 for r in results if r["all_home_types_extracted"])
        successful_detached = sum(1 for r in results if r["detached_extracted"])
        
        logger.info(f"Total PDFs processed: {total_pdfs}")
        logger.info(
            f"Successfully extracted ALL HOME TYPES: {successful_all_homes}/{total_pdfs} "
            f"({successful_all_homes / total_pdfs * 100:.1f}%)"
        )
        logger.info(
            f"Successfully extracted DETACHED: {successful_detached}/{total_pdfs} "
            f"({successful_detached / total_pdfs * 100:.1f}%)"
        )
        
        return summary_df


# Convenience function
def extract_all_pages() -> pd.DataFrame:
    """
    Extract all pages from all PDFs in the PDF directory.
    
    Returns:
        DataFrame summarizing the extraction results
    """
    extractor = PageExtractor()
    return extractor.process_all_pdfs()


def extract_specific_pdf(pdf_path: Path) -> Dict[str, bool]:
    """
    Extract pages from a specific PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with extraction results for each property type
    """
    extractor = PageExtractor()
    return extractor.process_pdf(pdf_path)
