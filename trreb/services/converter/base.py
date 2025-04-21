"""
Base classes for TRREB data table extractors.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from trreb.utils.logging import logger


class TableExtractor(ABC):
    """Abstract base class for TRREB data table extractors."""
    
    def __init__(self, property_type: str):
        """
        Initialize the extractor.
        
        Args:
            property_type: Type of property data to extract (all_home_types or detached)
        """
        self.property_type = property_type
    
    @abstractmethod
    def extract_table(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extract table data from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DataFrame containing the extracted table data
        """
        pass
    
    @abstractmethod
    def clean_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the extracted table data.
        
        Args:
            df: DataFrame containing the raw extracted table data
            
        Returns:
            Cleaned and standardized DataFrame
        """
        pass
    
    def process_pdf(self, pdf_path: Path, output_path: Path, overwrite: bool = False) -> Tuple[bool, Tuple[int, int]]:
        """
        Extract table from PDF and save as CSV.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Path to save the CSV output
            overwrite: Whether to overwrite existing output file
            
        Returns:
            Tuple of (success, (num_rows, num_cols))
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Fast path: Check if the output file already exists before any processing
        if output_path.exists() and not overwrite:
            logger.info(f"CSV file {output_path} already exists. Skipping conversion.")
            # Try to read the existing file to get its shape for consistent reporting
            try:
                existing_df = pd.read_csv(output_path)
                return True, existing_df.shape
            except Exception as e:
                logger.warning(f"Could not read existing CSV {output_path}: {e}")
                return True, (0, 0)  # Return success but unknown shape
        
        try:
            # Extract table
            logger.info(f"Extracting table from {pdf_path}")
            df = self.extract_table(pdf_path)
            
            # Clean and standardize the table
            if df is not None and not df.empty:
                df = self.clean_table(df)
                df.to_csv(output_path, index=False)
                logger.info(f"Saved table to {output_path}")
                return True, df.shape
            else:
                logger.warning(f"Failed to extract table from {pdf_path}")
                return False, (0, 0)
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return False, (0, 0)
