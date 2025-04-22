"""
Convert command for TRREB data extractor CLI.
This command handles the conversion of PDF files to CSV format.
"""

import click
import pandas as pd
from tqdm import tqdm

from trreb.services.converter import get_table_extractor
from trreb.utils.logging import logger
from trreb.utils.paths import (
    extract_date_from_filename,
    get_all_extracted_paths,
    get_output_paths,
)


@click.command()
@click.option(
    "--type",
    "property_type",
    type=click.Choice(["all_home_types", "detached"]),
    required=True,
    help="Type of property data to convert.",
)
@click.option(
    "--date",
    type=str,
    help="Specific date to convert (YYYY-MM format).",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing CSV files.",
)
def convert(property_type: str, date: str, overwrite: bool) -> None:
    """Convert extracted PDF pages into CSV format."""
    logger.info(f"Starting convert command for {property_type}")

    # Get all extracted files
    extracted_files = get_all_extracted_paths(property_type)

    # Filter by date if specified
    if date:
        logger.info(f"Filtering extracted files for date: {date}")
        extracted_files = [
            f
            for f in extracted_files
            if extract_date_from_filename(f.name) == date
        ]

    if not extracted_files:
        logger.error(f"No extracted files found for property type '{property_type}'.")
        return

    # Process each file
    results = []
    for pdf_path in tqdm(extracted_files, desc=f"Converting {property_type} files"):
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

    # Create a summary DataFrame
    summary_df = pd.DataFrame(results)

    # Print statistics
    total_files = len(results)
    successful_files = summary_df["success"].sum()

    logger.success("\nConversion complete!")
    logger.info(f"Total files converted: {total_files}")
    logger.info(
        f"Successfully converted: {successful_files}/{total_files} "
        f"({successful_files / total_files * 100:.1f}%)"
    )


def convert_type(property_type: str, overwrite: bool = False) -> list:
    """
    Convert all extracted pages for a specific property type.

    Args:
        property_type: Type of property (all_home_types or detached)
        overwrite: Whether to overwrite existing CSV files

    Returns:
        List of successfully converted files
    """
    # Get all extracted files
    extracted_files = get_all_extracted_paths(property_type)

    if not extracted_files:
        logger.error(f"No extracted files found for property type '{property_type}'.")
        return []

    # Process each file
    results = []
    for pdf_path in tqdm(extracted_files, desc=f"Converting {property_type} files"):
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

    logger.info(f"Total files converted: {total_files}")
    logger.info(
        f"Successfully converted: {successful_files}/{total_files} "
        f"({successful_files / total_files * 100:.1f}%)"
    )

    # Return list of successful conversions
    return [r for r in results if r["success"]]