#!/usr/bin/env python3
"""
Main script to run the complete TRREB data pipeline.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Add the parent directory to the Python path to allow importing trreb package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import dependencies here to avoid circular imports
from trreb.downloader.trreb_downloader import download_reports
from trreb.economic.integration import enrich_all_datasets
from trreb.extractor.page_extractor import PageExtractor
from trreb.utils.logging import setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the complete TRREB data pipeline.")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading PDFs")
    parser.add_argument("--skip-extract", action="store_true", help="Skip extracting pages")
    parser.add_argument("--skip-process", action="store_true", help="Skip processing CSVs")
    parser.add_argument("--skip-economic", action="store_true", help="Skip economic data integration")
    parser.add_argument("--validate", action="store_true", help="Validate data after processing")
    parser.add_argument("--normalize", action="store_true", help="Normalize data after processing")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="Set the logging level")
    return parser.parse_args()


def main():
    """Run the complete TRREB data pipeline."""
    args = parse_args()
    
    # Setup logger
    logger = setup_logger("trreb", level=args.log_level)
    
    logger.info("Starting TRREB data pipeline")
    
    # 1. Download PDFs if not skipped
    if not args.skip_download:
        logger.info("=== Downloading PDFs ===")
        downloaded_files = download_reports()
        logger.info(f"Downloaded {len(downloaded_files)} files")
    
    # 2. Extract pages if not skipped
    if not args.skip_extract:
        logger.info("=== Extracting Pages ===")
        extractor = PageExtractor()
        summary_df = extractor.process_all_pdfs()
        
        # Print statistics
        total_pdfs = len(summary_df)
        successful_all_homes = summary_df["all_home_types_extracted"].sum()
        successful_detached = summary_df["detached_extracted"].sum()
        
        logger.info(f"Total PDFs processed: {total_pdfs}")
        logger.info(f"Successfully extracted ALL HOME TYPES: {successful_all_homes}/{total_pdfs} "
              f"({successful_all_homes / total_pdfs * 100:.1f}%)")
        logger.info(f"Successfully extracted DETACHED: {successful_detached}/{total_pdfs} "
               f"({successful_detached / total_pdfs * 100:.1f}%)")
    
    # 3. Process CSVs if not skipped
    if not args.skip_process:
        # Get the process_type function, avoiding circular imports
        from trreb.cli.commands import process_type
        
        logger.info("=== Processing All Home Types ===")
        process_type("all_home_types", args.validate, args.normalize)
        
        logger.info("=== Processing Detached Homes ===")
        process_type("detached", args.validate, args.normalize)
    
    # 4. Integrate economic data if not skipped
    if not args.skip_economic:
        logger.info("=== Integrating Economic Data ===")
        enriched_data = enrich_all_datasets()
        
        for property_type, df in enriched_data.items():
            logger.info(f"Enriched {property_type} dataset with {len(df)} rows and {len(df.columns)} columns")
    
    logger.info("=== Pipeline Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
