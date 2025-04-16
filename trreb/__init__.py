"""
TRREB Data Extractor - A tool for extracting, processing, and analyzing Toronto Regional Real Estate Board data.
"""

import os
from pathlib import Path

# Version information
__version__ = "0.1.0"

# Import key functionality for easy access
from trreb.downloader.trreb_downloader import download_reports
from trreb.extractor import extract_all_pages, get_extractor, process_pdf
from trreb.processor.normalization import normalize_dataset
from trreb.processor.validation import generate_validation_report
from trreb.economic.integration import enrich_trreb_data, enrich_all_datasets

# Define high-level convenience functions
def download_data(start_year=None):
    """
    Download TRREB market reports.
    
    Args:
        start_year: First year to download (optional)
    
    Returns:
        List of paths to downloaded files
    """
    return download_reports(start_year)

def extract_data():
    """
    Extract property data pages from all downloaded PDFs.
    
    Returns:
        DataFrame summarizing the extraction results
    """
    return extract_all_pages()

def process_data(property_type, validate=True, normalize=True):
    """
    Process extracted pages into structured CSV format.
    
    Args:
        property_type: Type of property (all_home_types or detached)
        validate: Whether to validate the data
        normalize: Whether to normalize the data
    
    Returns:
        Path to the processed data file
    """
    from trreb.cli.commands import process_type
    return process_type(property_type, validate, normalize)

def enrich_data(property_type, include_lags=True):
    """
    Enrich TRREB data with economic indicators.
    
    Args:
        property_type: Type of property (all_home_types or detached)
        include_lags: Whether to include lagged economic indicators
    
    Returns:
        DataFrame containing enriched data
    """
    return enrich_trreb_data(property_type, include_lags)

def run_full_pipeline(skip_download=False, skip_extract=False, 
                     skip_process=False, skip_economic=False,
                     validate=True, normalize=True):
    """
    Run the complete data pipeline.
    
    Args:
        skip_download: Whether to skip downloading PDFs
        skip_extract: Whether to skip extracting pages
        skip_process: Whether to skip processing CSVs
        skip_economic: Whether to skip economic data integration
        validate: Whether to validate the data
        normalize: Whether to normalize the data
    
    Returns:
        Dictionary of property type to enriched DataFrame
    """
    # Import only when needed to avoid circular imports
    from scripts.run_pipeline import main
    
    # Run the pipeline
    return main()

__all__ = [
    "__version__",
    "download_data",
    "extract_data",
    "process_data",
    "enrich_data",
    "run_full_pipeline",
    "normalize_dataset",
    "generate_validation_report",
]
