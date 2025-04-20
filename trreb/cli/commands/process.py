"""
Process command for TRREB data extractor CLI.
"""

import argparse
import pandas as pd
from tqdm import tqdm

from trreb.config import PROCESSED_DIR
from trreb.services.csv_converter import get_table_extractor
from trreb.services.data_processor.normalization import normalize_dataset
from trreb.services.data_processor.validation import generate_validation_report
from trreb.utils.logging import logger
from trreb.utils.paths import (
    extract_date_from_filename,
    get_all_extracted_paths,
    get_output_paths,
)


def process(args: argparse.Namespace):
    """
    CLI command to process extracted pages into CSV format.
    Accepts parsed arguments from __main__.py.
    """
    # Logger is already set up in __main__.py
    logger.info(f"Starting process command with args: {args}")

    property_type = args.type

    # Get all extracted files
    extracted_files = get_all_extracted_paths(property_type)

    # Filter by date if specified
    if args.date:
        logger.info(f"Filtering extracted files for date: {args.date}")
        extracted_files = [
            f
            for f in extracted_files
            if extract_date_from_filename(f.name) == args.date
        ]

    if not extracted_files:
        logger.error(f"No extracted files found for property type '{property_type}'.")
        return 1

    # Process each file
    results = []
    for pdf_path in tqdm(extracted_files, desc=f"Processing {property_type} files"):
        date_str = extract_date_from_filename(pdf_path.name)
        if not date_str:
            logger.warning(f"Could not extract date from {pdf_path.name}. Skipping.")
            continue

        # Get appropriate extractor
        extractor = get_table_extractor(date_str, property_type)

        # Get output path
        _, output_path = get_output_paths(date_str, property_type)

        # Process the file
        success, shape = extractor.process_pdf(pdf_path, output_path, args.overwrite)

        # Add to results
        results.append(
            {
                "filename": pdf_path.name,
                "date": date_str,
                "success": success,
                "num_rows": shape[0],
                "num_cols": shape[1],
            }
        )

    # Create a summary DataFrame
    summary_df = pd.DataFrame(results)

    # Print statistics
    total_files = len(results)
    successful_files = summary_df["success"].sum()

    logger.success("\nProcessing complete!")
    logger.info(f"Total files processed: {total_files}")
    logger.info(
        f"Successfully processed: {successful_files}/{total_files} "
        f"({successful_files / total_files * 100:.1f}%)"
    )

    # Validate and normalize if requested
    normalized_path = None
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
            logger.warning("No data to validate or normalize.")
            return 0

        combined_df = pd.concat(all_data, ignore_index=True)

        # Validate if requested
        if args.validate:
            validation_result = generate_validation_report(combined_df, date_col="date")
            logger.info("\nValidation Report:")
            logger.info(validation_result)

        # Normalize if requested
        if args.normalize:
            logger.info("\nNormalizing data...")
            normalized_df = normalize_dataset(combined_df, date_col="date")

            # Save normalized data
            normalized_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
            normalized_df.to_csv(normalized_path, index=False)
            logger.success(f"Normalized data saved to {normalized_path}")

    return 0


def process_type(
    property_type: str,
    validate: bool = False,
    normalize: bool = False,
    overwrite: bool = False,
):
    """
    Process all extracted pages for a specific property type.

    Args:
        property_type: Type of property (all_home_types or detached)
        validate: Whether to validate the data
        normalize: Whether to normalize the data
        overwrite: Whether to overwrite existing CSV files

    Returns:
        Path to normalized data file if normalize=True, otherwise None
    """
    # Get all extracted files
    extracted_files = get_all_extracted_paths(property_type)

    if not extracted_files:
        logger.error(f"No extracted files found for property type '{property_type}'.")
        return None

    # Process each file
    results = []
    for pdf_path in tqdm(extracted_files, desc=f"Processing {property_type} files"):
        date_str = extract_date_from_filename(pdf_path.name)
        if not date_str:
            logger.warning(f"Could not extract date from {pdf_path.name}. Skipping.")
            continue

        # Get appropriate extractor
        extractor = get_table_extractor(date_str, property_type)

        # Get output path
        _, output_path = get_output_paths(date_str, property_type)

        # Process the file
        success, shape = extractor.process_pdf(pdf_path, output_path, overwrite)

        # Add to results
        results.append(
            {
                "filename": pdf_path.name,
                "date": date_str,
                "success": success,
                "num_rows": shape[0],
                "num_cols": shape[1],
            }
        )

    # Print statistics
    total_files = len(results)
    successful_files = sum(1 for r in results if r["success"])

    logger.info(f"Total files processed: {total_files}")
    logger.info(
        f"Successfully processed: {successful_files}/{total_files} "
        f"({successful_files / total_files * 100:.1f}%)"
    )

    # Validate and normalize if requested
    normalized_path = None
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
            logger.warning("No data to validate or normalize.")
            return None

        combined_df = pd.concat(all_data, ignore_index=True)

        # Validate if requested
        if validate:
            validation_result = generate_validation_report(combined_df, date_col="date")
            logger.info("\nValidation Report:")
            logger.info(validation_result)

        # Normalize if requested
        if normalize:
            logger.info("\nNormalizing data...")
            normalized_df = normalize_dataset(combined_df, date_col="date")

            # Save normalized data
            normalized_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
            normalized_df.to_csv(normalized_path, index=False)
            logger.success(f"Normalized data saved to {normalized_path}")

    return normalized_path
