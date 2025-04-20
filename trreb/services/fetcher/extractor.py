"""
Module for extracting specific pages from TRREB market reports.
"""

import os
from pathlib import Path
from typing import Dict, Optional

import PyPDF2

from trreb.config import ALL_HOMES_EXTRACTED_DIR, DETACHED_EXTRACTED_DIR
from trreb.utils.logging import logger
from trreb.utils.paths import extract_date_from_filename
from trreb.services.fetcher.identifier import PageIdentifier


class PageExtractor:
    """
    Class for extracting specific pages from TRREB market report PDFs.
    
    Extracts pages containing:
    - ALL HOME TYPES data
    - DETACHED homes data
    
    Saves extracted pages to separate directories.
    """
    
    def __init__(
        self, 
        identifier: Optional[PageIdentifier] = None,
        all_homes_dir: Path = ALL_HOMES_EXTRACTED_DIR,
        detached_dir: Path = DETACHED_EXTRACTED_DIR
    ):
        """
        Initialize the page extractor.
        
        Args:
            identifier: Optional PageIdentifier instance for page identification
            all_homes_dir: Directory to save ALL HOME TYPES pages
            detached_dir: Directory to save DETACHED pages
        """
        self.identifier = identifier or PageIdentifier()
        self.all_homes_dir = all_homes_dir
        self.detached_dir = detached_dir
        
        # Create directories if they don't exist
        os.makedirs(self.all_homes_dir, exist_ok=True)
        os.makedirs(self.detached_dir, exist_ok=True)
    
    def extract_page(
        self, 
        pdf_path: Path, 
        page_num: Optional[int], 
        output_path: Path, 
        overwrite: bool = False
    ) -> bool:
        """
        Extract a specific page as a new PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number to extract (0-indexed)
            output_path: Path to save the extracted page
            overwrite: Whether to overwrite existing output file
            
        Returns:
            True if successful, False otherwise
        """
        if page_num is None:
            logger.warning(f"No page number specified for {pdf_path}")
            return False
        
        # Check if the output file already exists and we don't want to overwrite
        if output_path.exists() and not overwrite:
            logger.info(f"Output file {output_path} already exists. Skipping extraction.")
            return True  # Return True since the file exists as required
        
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
    
    def extract_pdf_pages(self, pdf_path: Path, overwrite: bool = False) -> Dict[str, bool]:
        """
        Process a single PDF file to extract relevant pages.
        
        Args:
            pdf_path: Path to the PDF file
            overwrite: Whether to overwrite existing output files
            
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
        
        # Determine output paths
        all_homes_path = self.all_homes_dir / f"{date_str}.pdf"
        detached_path = self.detached_dir / f"{date_str}.pdf"
        
        # Skip page identification if both files exist and we're not overwriting
        if not overwrite and all_homes_path.exists() and detached_path.exists():
            logger.info(f"  ✓ ALL HOME TYPES page already exists at {all_homes_path.name}")
            logger.info(f"  ✓ DETACHED page already exists at {detached_path.name}")
            return {"all_home_types_extracted": True, "detached_extracted": True}
        
        # Identify page types only if needed
        page_info = self.identifier.identify_pages(pdf_path)
        
        # Extract and save pages with unique filenames to type-specific folders
        if page_info["all_home_types"] is not None:
            result["all_home_types_extracted"] = self.extract_page(
                pdf_path, page_info["all_home_types"], all_homes_path, overwrite
            )
            if result["all_home_types_extracted"]:
                if all_homes_path.exists() and not overwrite:
                    logger.info(f"  ✓ ALL HOME TYPES page already exists at {all_homes_path.name}")
                else:
                    logger.info(f"  ✓ ALL HOME TYPES page extracted to {all_homes_path.name}")
            else:
                logger.warning(f"  ✗ Failed to extract ALL HOME TYPES page")
        else:
            logger.warning(f"  ✗ ALL HOME TYPES page not found")
        
        if page_info["detached"] is not None:
            result["detached_extracted"] = self.extract_page(
                pdf_path, page_info["detached"], detached_path, overwrite
            )
            if result["detached_extracted"]:
                if detached_path.exists() and not overwrite:
                    logger.info(f"  ✓ DETACHED page already exists at {detached_path.name}")
                else:
                    logger.info(f"  ✓ DETACHED page extracted to {detached_path.name}")
            else:
                logger.warning(f"  ✗ Failed to extract DETACHED page")
        else:
            logger.warning(f"  ✗ DETACHED page not found")
        
        return result


# Convenience function for direct usage
def extract_page_from_pdf(pdf_path: Path, overwrite: bool = False) -> Dict[str, bool]:
    """
    Extract relevant pages from a specific PDF.
    
    Args:
        pdf_path: Path to the PDF file
        overwrite: Whether to overwrite existing output files
        
    Returns:
        Dictionary with extraction results for each property type
    """
    extractor = PageExtractor()
    return extractor.extract_pdf_pages(pdf_path, overwrite)
