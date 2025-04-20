"""
Module for generating reports on PDF extraction results.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from trreb.config import ALL_HOMES_EXTRACTED_DIR, DETACHED_EXTRACTED_DIR, PDF_DIR
from trreb.utils.logging import logger
from trreb.utils.paths import extract_date_from_filename
from trreb.services.fetcher.extractor import PageExtractor


class ExtractionReport:
    """
    Class for generating reports on PDF extraction results.
    
    Creates summaries of:
    - PDFs processed
    - Successful extractions
    - Missing pages
    - Overall statistics
    """
    
    def __init__(
        self,
        pdf_dir: Path = PDF_DIR,
        all_homes_dir: Path = ALL_HOMES_EXTRACTED_DIR,
        detached_dir: Path = DETACHED_EXTRACTED_DIR,
        extractor: Optional[PageExtractor] = None
    ):
        """
        Initialize the extraction report generator.
        
        Args:
            pdf_dir: Directory containing PDF files
            all_homes_dir: Directory for ALL HOME TYPES pages
            detached_dir: Directory for DETACHED pages
            extractor: Optional PageExtractor instance
        """
        self.pdf_dir = pdf_dir
        self.all_homes_dir = all_homes_dir
        self.detached_dir = detached_dir
        self.extractor = extractor or PageExtractor(
            all_homes_dir=all_homes_dir,
            detached_dir=detached_dir
        )
    
    def generate_report(self, overwrite: bool = False) -> pd.DataFrame:
        """
        Process all PDF files and generate a summary report.
        
        Args:
            overwrite: Whether to overwrite existing extracted files
            
        Returns:
            DataFrame summarizing the extraction results
        """
        results = []
        
        # Get all PDF files
        pdf_files = sorted([f for f in os.listdir(self.pdf_dir) if f.lower().endswith(".pdf")])
        
        for pdf_file in pdf_files:
            pdf_path = self.pdf_dir / pdf_file
            
            # Get date from filename
            date_str = extract_date_from_filename(pdf_file)
            if not date_str:
                # Use original filename as fallback
                logger.warning(f"Could not extract date from {pdf_file}. Using filename as identifier.")
                date_str = os.path.splitext(pdf_file)[0]
            
            # Determine target paths
            all_homes_path = self.all_homes_dir / f"{date_str}.pdf"
            detached_path = self.detached_dir / f"{date_str}.pdf"
            
            # Check if both files already exist and we're not overwriting
            all_exists = all_homes_path.exists()
            det_exists = detached_path.exists()
            
            if not overwrite and all_exists and det_exists:
                # Fast path: Skip PDF processing completely
                logger.info(f"Processing {pdf_file} (Date: {date_str})...")
                logger.info(f"  ✓ ALL HOME TYPES page already exists at {date_str}.pdf")
                logger.info(f"  ✓ DETACHED page already exists at {date_str}.pdf")
                
                results.append({
                    "filename": pdf_file,
                    "date": date_str,
                    "all_home_types_page": 0,  # Dummy value, not actually used
                    "all_home_types_extracted": True,
                    "detached_page": 0,  # Dummy value, not actually used
                    "detached_extracted": True,
                })
                continue
            
            # Process the PDF if needed
            result = self.extractor.extract_pdf_pages(pdf_path, overwrite)
            
            # Add to results
            results.append({
                "filename": pdf_file,
                "date": date_str,
                "all_home_types_page": None,  # We don't track the specific page numbers in the report
                "all_home_types_extracted": result["all_home_types_extracted"],
                "detached_page": None,  # We don't track the specific page numbers in the report
                "detached_extracted": result["detached_extracted"],
            })
        
        # Create a summary DataFrame
        summary_df = pd.DataFrame(results)
        summary_path = self.all_homes_dir.parent / "extraction_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        
        logger.info(f"Extraction complete! Summary saved to {summary_path}")
        
        # Print statistics
        self._log_statistics(results)
        
        return summary_df
    
    def _log_statistics(self, results: List[Dict]) -> None:
        """
        Log statistics about the extraction results.
        
        Args:
            results: List of extraction result dictionaries
        """
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


# Convenience function for direct usage
def extract_all_pdfs(overwrite: bool = False) -> pd.DataFrame:
    """
    Process all PDF files in the default directory and generate a summary report.
    
    Args:
        overwrite: Whether to overwrite existing output files
        
    Returns:
        DataFrame summarizing the extraction results
    """
    report_generator = ExtractionReport()
    return report_generator.generate_report(overwrite)
