"""
Normalize command for TRREB data extractor CLI.
This command handles the normalization of CSV data.
"""

import argparse
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from trreb.config import PROCESSED_DIR
from trreb.services.data_processor.normalization import normalize_dataset
from trreb.services.data_processor.validation import generate_validation_report
from trreb.utils.logging import logger
from trreb.utils.paths import get_output_paths


def normalize(args: argparse.Namespace):
    """
    CLI command to normalize processed CSV data.
    Accepts parsed arguments from __main__.py.
    """
    # Logger is already set up in __main__.py
    logger.info(f"Starting normalize command with args: {args}")

    property_type = args.type

    # Process the data for normalization
    normalized_path = normalize_type(
        property_type=property_type,
        validate=args.validate,
        date=args.date,
    )

    if normalized_path:
        logger.success(f"Normalized data saved to {normalized_path}")
        return 0
    else:
        logger.error("Normalization failed.")
        return 1


def normalize_type(
    property_type: str,
    validate: bool = False,
    date: str = None,
):
    """
    Normalize processed CSVs for a specific property type.

    Args:
        property_type: Type of property (all_home_types or detached)
        validate: Whether to validate the data
        date: Specific date to process (e.g., "2020-01")

    Returns:
        Path to normalized data file if successful, otherwise None
    """
    # Find all CSV files matching the property type
    csv_files = []
    processed_dir = PROCESSED_DIR
    
    # Get all CSV files for this property type
    for csv_path in processed_dir.glob(f"*_{property_type}.csv"):
        # Skip already normalized files
        if "normalized" in csv_path.name:
            continue
            
        # If date is specified, filter by it
        if date:
            if date not in csv_path.name:
                continue
        
        csv_files.append(csv_path)
    
    if not csv_files:
        logger.error(f"No CSV files found for property type '{property_type}'.")
        return None

    # Combine all processed CSVs
    all_data = []
    for csv_path in tqdm(csv_files, desc=f"Reading {property_type} files"):
        try:
            df = pd.read_csv(csv_path)
            # Extract date from filename if it's not already in the data
            if "date" not in df.columns:
                # Try to extract date from filename
                date_str = csv_path.stem.split("_")[0]
                if date_str and len(date_str) == 6:  # 'YYYYMM' format
                    date_str = f"{date_str[:4]}-{date_str[4:]}"
                    df["date"] = date_str
                else:
                    logger.warning(f"Could not extract date from {csv_path.name}. Using filename as date.")
                    df["date"] = csv_path.stem
            all_data.append(df)
        except Exception as e:
            logger.error(f"Error reading {csv_path}: {e}")

    if not all_data:
        logger.warning("No data to normalize.")
        return None

    combined_df = pd.concat(all_data, ignore_index=True)

    # Validate if requested
    if validate:
        validation_result = generate_validation_report(combined_df, date_col="date")
        logger.info("\nValidation Report:")
        logger.info(validation_result)

    # Normalize the data
    logger.info("\nNormalizing data...")
    normalized_df = normalize_dataset(combined_df, date_col="date")

    # Save normalized data
    normalized_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
    normalized_df.to_csv(normalized_path, index=False)
    logger.success(f"Normalized data saved to {normalized_path}")

    return normalized_path
