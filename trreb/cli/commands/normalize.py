"""
Normalize command for TRREB data extractor CLI.
This command handles the normalization of CSV data.
"""

import argparse
import pandas as pd
from tqdm import tqdm

from trreb.config import PROCESSED_DIR
from trreb.services.normalizer.normalization import normalize_dataset
from trreb.services.normalizer.validation import generate_validation_report
from trreb.utils.logging import logger


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
    processed_dir = PROCESSED_DIR / property_type

    # Get all CSV files for this property type
    for csv_path in processed_dir.glob("*.csv"):
        # Skip already normalized files
        if "normalized" in csv_path.name:
            continue

        # If date is specified, filter by it
        if date:
            if date not in csv_path.name:
                continue

        csv_files.append(csv_path)

    csv_files = sorted(csv_files)

    logger.info(f"Found {len(csv_files)} CSV files for property type '{property_type}'")

    if not csv_files:
        logger.error(f"No CSV files found for property type '{property_type}'.")
        return None

    # Process each CSV file
    all_data = []
    for csv_path in tqdm(csv_files, desc=f"Reading {property_type} files"):
        try:
            try:
                # First try with default engine but skip bad lines
                df = pd.read_csv(
                    csv_path, quotechar='"', escapechar="\\", on_bad_lines="skip"
                )
            except Exception as e1:
                logger.warning(
                    f"Standard parsing failed for {csv_path}: {e1}. Trying with Python engine."
                )
                try:
                    # Try with Python engine which is more forgiving
                    df = pd.read_csv(
                        csv_path, quotechar='"', escapechar="\\", engine="python"
                    )
                except Exception as e2:
                    logger.warning(
                        f"Python engine failed for {csv_path}: {e2}. Trying with flexible delimiter detection."
                    )
                    # Last resort: try to read with even more flexible options
                    df = pd.read_csv(
                        csv_path,
                        sep=None,  # Auto-detect separator
                        quotechar='"',
                        escapechar="\\",
                        engine="python",
                        on_bad_lines="skip",
                    )

            # Extract date from filename (e.g., "2020-10.csv" -> "2020-10")
            file_date_str = csv_path.stem
            df["date_str"] = file_date_str  # get filename without extension

            df = normalize_dataset(
                df=df,
                date_str=file_date_str,
                property_type=property_type,
            )
            all_data.append(df)
        except Exception as e:
            logger.error(f"Error reading {csv_path}: {e}")

    if not all_data:
        logger.warning("No data to normalize.")
        return None

    # Combine all DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)

    # Handle duplicate columns resulting from combining different file formats
    # Get a clean version with standardized columns
    if combined_df is not None and not combined_df.empty:
        # Identify duplicate columns (excluding the first region column)
        duplicate_cols = []
        seen_cols = set()
        for col in combined_df.columns:
            col_name = str(col).strip() if col is not None else ""
            if col_name in seen_cols and col != combined_df.columns[0]:
                duplicate_cols.append(col)
            else:
                seen_cols.add(col_name)

        # Drop duplicate columns
        if duplicate_cols:
            logger.warning(f"Dropping duplicate columns: {duplicate_cols}")
            combined_df = combined_df.drop(columns=duplicate_cols)

        # Validate if requested
        if validate:
            validation_result = generate_validation_report(
                df=combined_df,
                date_col="date",
                property_type=property_type,
                date_str=date if date else None,
            )
            logger.info("\nValidation Report:")
            logger.info(validation_result)

        # Final normalization pass on the combined data
        logger.info("\nNormalizing data...")
        normalized_df = normalize_dataset(
            df=combined_df,
            date_col="date",
            property_type=property_type,
            date_str=date if date else None,
        )

        # For all_home_types, specifically remove any Unnamed: 12-14 columns that might still exist
        if property_type == "all_home_types":
            specific_cols_to_drop = [
                col
                for col in normalized_df.columns
                if col in ["Unnamed: 12", "Unnamed: 13", "Unnamed: 14"]
            ]
            if specific_cols_to_drop:
                logger.info(f"Removing specific empty columns: {specific_cols_to_drop}")
                normalized_df = normalized_df.drop(columns=specific_cols_to_drop)

        logger.info("Sorting data by region type, year, and month")

        # Create a region_type_order column for proper sorting
        region_type_order = {
            "Total": 0,  # TRREB Total first
            "Region": 1,  # Regions next (Halton, Peel, etc.)
            "Municipality": 2,  # Municipalities last
        }

        # Create temporary column for sorting
        normalized_df["_sort_order"] = (
            normalized_df["region_type"].map(region_type_order).fillna(3)
        )

        # First sort by region_type to group regions logically (Total, Region, Municipality)
        # Then sort by year and month for chronological ordering within each region
        # Then sort by the original region column to keep regions together
        normalized_df = normalized_df.sort_values(
            by=["_sort_order", "parent_region", "Region", "date_str"]
        )

        # Drop the temporary sorting column
        normalized_df = normalized_df.drop(columns=["_sort_order"])

        # Reset index to have clean row numbers after sorting
        normalized_df = normalized_df.reset_index(drop=True)

        # Filter out non-region rows (numeric/junk values in Region column)
        # We only want to keep real region names
        valid_regions = (
            normalized_df["region_type"].isin(["Total", "Region", "Municipality"])
            & normalized_df["Region"].notna()
            & ~normalized_df["Region"]
            .astype(str)
            .str.match(r"^\d+(\.\d+)?$")  # Exclude numeric values
        )
        logger.info(f"Filtering out {(~valid_regions).sum()} invalid region rows")
        normalized_df = normalized_df[valid_regions]

        # Save normalized data
        normalized_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
        normalized_df.to_csv(normalized_path, index=False)
        logger.success(f"Normalized data saved to {normalized_path}")

        return normalized_path
    else:
        logger.error("No valid data to normalize after processing files.")
        return None
