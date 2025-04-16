"""
Command-line interface for TRREB data extractor.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from tqdm import tqdm

from trreb.downloader.trreb_downloader import download_reports
from trreb.extractor import extract_all_pages, get_extractor, process_pdf
from trreb.extractor.page_extractor import PageExtractor
from trreb.processor.normalization import normalize_dataset
from trreb.processor.validation import generate_validation_report
from trreb.utils.logging import logger, setup_logger
from trreb.utils.paths import extract_date_from_filename, get_all_extracted_paths, get_output_paths


def download():
    """CLI command to download TRREB PDFs."""
    parser = argparse.ArgumentParser(description="Download TRREB market reports.")
    parser.add_argument("--start-year", type=int, help="First year to download (default: 2016)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logger
    setup_logger("trreb", level=getattr(logging, args.log_level))
    
    # Download reports
    if args.start_year:
        downloaded_files = download_reports(args.start_year)
    else:
        downloaded_files = download_reports()
    
    # Print summary
    print(f"\nDownload complete! Downloaded {len(downloaded_files)} files.")
    
    return 0


def extract_pages():
    """CLI command to extract pages from PDFs."""
    parser = argparse.ArgumentParser(description="Extract specific pages from TRREB PDFs.")
    parser.add_argument("--pdf", help="Process a specific PDF file (default: process all PDFs)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logger
    setup_logger("trreb", level=getattr(logging, args.log_level))
    
    # Create page extractor
    extractor = PageExtractor()
    
    # Process PDFs
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: PDF file {pdf_path} not found.")
            return 1
        
        result = extractor.process_pdf(pdf_path)
        
        # Print result
        if result["all_home_types_extracted"]:
            print(f"✓ ALL HOME TYPES page extracted.")
        else:
            print(f"✗ Failed to extract ALL HOME TYPES page.")
            
        if result["detached_extracted"]:
            print(f"✓ DETACHED page extracted.")
        else:
            print(f"✗ Failed to extract DETACHED page.")
    else:
        # Process all PDFs
        summary_df = extractor.process_all_pdfs()
        
        # Print statistics
        total_pdfs = len(summary_df)
        successful_all_homes = summary_df["all_home_types_extracted"].sum()
        successful_detached = summary_df["detached_extracted"].sum()
        
        print(f"\nExtraction complete!")
        print(f"Total PDFs processed: {total_pdfs}")
        print(f"Successfully extracted ALL HOME TYPES: {successful_all_homes}/{total_pdfs} "
              f"({successful_all_homes / total_pdfs * 100:.1f}%)")
        print(f"Successfully extracted DETACHED: {successful_detached}/{total_pdfs} "
              f"({successful_detached / total_pdfs * 100:.1f}%)")
    
    return 0


def process():
    """CLI command to process extracted pages into CSV format."""
    parser = argparse.ArgumentParser(description="Process extracted pages into CSV format.")
    parser.add_argument("--type", choices=["all_home_types", "detached"], required=True,
                        help="Type of property data to process")
    parser.add_argument("--date", help="Process a specific date (e.g., 2020-01)")
    parser.add_argument("--validate", action="store_true", help="Validate data after processing")
    parser.add_argument("--normalize", action="store_true", help="Normalize data after processing")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logger
    setup_logger("trreb", level=getattr(logging, args.log_level))
    
    property_type = args.type
    
    # Get all extracted files
    extracted_files = get_all_extracted_paths(property_type)
    
    # Filter by date if specified
    if args.date:
        extracted_files = [f for f in extracted_files if extract_date_from_filename(f.name) == args.date]
    
    if not extracted_files:
        print(f"No extracted files found for property type '{property_type}'.")
        return 1
    
    # Process each file
    results = []
    for pdf_path in tqdm(extracted_files, desc=f"Processing {property_type} files"):
        date_str = extract_date_from_filename(pdf_path.name)
        if not date_str:
            logger.warning(f"Could not extract date from {pdf_path.name}. Skipping.")
            continue
        
        # Get appropriate extractor
        extractor = get_extractor(date_str, property_type)
        
        # Get output path
        _, output_path = get_output_paths(date_str, property_type)
        
        # Process the file
        success, shape = extractor.process_pdf(pdf_path, output_path)
        
        # Add to results
        results.append({
            "filename": pdf_path.name,
            "date": date_str,
            "success": success,
            "num_rows": shape[0],
            "num_cols": shape[1],
        })
    
    # Create a summary DataFrame
    summary_df = pd.DataFrame(results)
    
    # Print statistics
    total_files = len(results)
    successful_files = summary_df["success"].sum()
    
    print(f"\nProcessing complete!")
    print(f"Total files processed: {total_files}")
    print(f"Successfully processed: {successful_files}/{total_files} "
          f"({successful_files / total_files * 100:.1f}%)")
    
    # Validate and normalize if requested
    if args.validate or args.normalize:
        # Combine all processed CSVs
        all_data = []
        for index, row in summary_df[summary_df["success"]].iterrows():
            _, csv_path = get_output_paths(row["date"], property_type)
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                    df["date"] = row["date"]
                    all_data.append(df)
                except Exception as e:
                    logger.error(f"Error reading {csv_path}: {e}")
        
        if not all_data:
            print("No data to validate or normalize.")
            return 0
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Validate if requested
        if args.validate:
            validation_result = generate_validation_report(combined_df, date_col="date")
            print("\nValidation Report:")
            print(validation_result)
        
        # Normalize if requested
        if args.normalize:
            print("\nNormalizing data...")
            normalized_df = normalize_dataset(combined_df, date_col="date")
            
            # Save normalized data
            from trreb.config import PROCESSED_DIR
            normalized_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
            normalized_df.to_csv(normalized_path, index=False)
            print(f"Normalized data saved to {normalized_path}")
    
    return 0


def run_pipeline():
    """CLI command to run the full pipeline."""
    parser = argparse.ArgumentParser(description="Run the full TRREB data extraction pipeline.")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading PDFs")
    parser.add_argument("--skip-extract", action="store_true", help="Skip extracting pages")
    parser.add_argument("--skip-process", action="store_true", help="Skip processing CSVs")
    parser.add_argument("--validate", action="store_true", help="Validate data after processing")
    parser.add_argument("--normalize", action="store_true", help="Normalize data after processing")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logger
    setup_logger("trreb", level=getattr(logging, args.log_level))
    
    # 1. Download PDFs if not skipped
    if not args.skip_download:
        print("\n=== Downloading PDFs ===")
        downloaded_files = download_reports()
        print(f"Downloaded {len(downloaded_files)} files.")
    
    # 2. Extract pages if not skipped
    if not args.skip_extract:
        print("\n=== Extracting Pages ===")
        extractor = PageExtractor()
        summary_df = extractor.process_all_pdfs()
    
    # 3. Process CSVs if not skipped
    if not args.skip_process:
        print("\n=== Processing All Home Types ===")
        process_type("all_home_types", args.validate, args.normalize)
        
        print("\n=== Processing Detached Homes ===")
        process_type("detached", args.validate, args.normalize)
    
    print("\n=== Pipeline Complete ===")
    return 0


def process_type(property_type: str, validate: bool = False, normalize: bool = False):
    """
    Process all extracted pages for a specific property type.
    
    Args:
        property_type: Type of property (all_home_types or detached)
        validate: Whether to validate the data
        normalize: Whether to normalize the data
    """
    # Get all extracted files
    extracted_files = get_all_extracted_paths(property_type)
    
    if not extracted_files:
        print(f"No extracted files found for property type '{property_type}'.")
        return
    
    # Process each file
    results = []
    for pdf_path in tqdm(extracted_files, desc=f"Processing {property_type} files"):
        date_str = extract_date_from_filename(pdf_path.name)
        if not date_str:
            logger.warning(f"Could not extract date from {pdf_path.name}. Skipping.")
            continue
        
        # Get appropriate extractor
        extractor = get_extractor(date_str, property_type)
        
        # Get output path
        _, output_path = get_output_paths(date_str, property_type)
        
        # Process the file
        success, shape = extractor.process_pdf(pdf_path, output_path)
        
        # Add to results
        results.append({
            "filename": pdf_path.name,
            "date": date_str,
            "success": success,
            "num_rows": shape[0],
            "num_cols": shape[1],
        })
    
    # Print statistics
    total_files = len(results)
    successful_files = sum(1 for r in results if r["success"])
    
    print(f"Total files processed: {total_files}")
    print(f"Successfully processed: {successful_files}/{total_files} "
          f"({successful_files / total_files * 100:.1f}%)")
    
    # Validate and normalize if requested
    if validate or normalize:
        # Combine all processed CSVs
        all_data = []
        for row in results:
            if row["success"]:
                _, csv_path = get_output_paths(row["date"], property_type)
                if csv_path.exists():
                    try:
                        df = pd.read_csv(csv_path)
                        df["date"] = row["date"]
                        all_data.append(df)
                    except Exception as e:
                        logger.error(f"Error reading {csv_path}: {e}")
        
        if not all_data:
            print("No data to validate or normalize.")
            return
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Validate if requested
        if validate:
            validation_result = generate_validation_report(combined_df, date_col="date")
            print("\nValidation Report:")
            print(validation_result)
        
        # Normalize if requested
        if normalize:
            print("\nNormalizing data...")
            normalized_df = normalize_dataset(combined_df, date_col="date")
            
            # Save normalized data
            from trreb.config import PROCESSED_DIR
            normalized_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
            normalized_df.to_csv(normalized_path, index=False)
            print(f"Normalized data saved to {normalized_path}")
