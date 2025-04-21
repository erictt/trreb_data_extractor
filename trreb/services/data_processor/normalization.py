"""
Data normalization utilities for TRREB data.
"""

from typing import Optional, Dict, List, Union
from datetime import datetime

import pandas as pd

from trreb.config import (
    COLUMN_NAME_MAPPING,
    REGION_HIERARCHY,
    REGION_NAME_MAPPING,
    PRE_2020_ALL_HOME_COLUMNS,
    PRE_2020_DETACHED_COLUMNS,
    MID_PERIOD_ALL_HOME_COLUMNS,
    MID_PERIOD_DETACHED_COLUMNS,
    POST_2022_ALL_HOME_COLUMNS,
    POST_2022_DETACHED_COLUMNS,
    EXTRACTION_CUTOFF_DATE,
    SECOND_FORMAT_CUTOFF_DATE,
)
from trreb.utils.logging import logger


def fix_numeric_regions(
    df: pd.DataFrame, date_str: Optional[str] = None
) -> pd.DataFrame:
    """
    Try to fix a DataFrame with numeric values in the region column
    by reconstructing the expected structure.

    Args:
        df: DataFrame to fix
        date_str: Date string to determine expected structure

    Returns:
        Fixed DataFrame, or original if can't be fixed
    """
    # If we don't have numeric values in the first column, no need to fix
    if df.empty or not pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
        return df

    try:
        logger.warning("Detected numeric values in region column, attempting to fix")

        # Use the standard region list for the first column
        # Start with the expected regions for key regions
        regions = [
            "TRREB Total",
            "Halton Region",
            "Burlington",
            "Halton Hills",
            "Milton",
            "Oakville",
            "Peel Region",
            "Brampton",
            "Caledon",
            "Mississauga",
            "City of Toronto",
            "Toronto West",
            "Toronto Central",
            "Toronto East",
            "York Region",
        ]

        # Determine number of rows to use based on the data
        n_rows = min(len(regions), len(df))

        # Create a new DataFrame with the expected regions
        fixed_df = pd.DataFrame({df.columns[0]: regions[:n_rows]})

        # Copy the numeric data
        for col in df.columns[1:]:
            if col in fixed_df.columns:
                # Avoid duplicate columns
                fixed_df[f"{col}_copy"] = df[col].iloc[:n_rows].values
            else:
                fixed_df[col] = df[col].iloc[:n_rows].values

        return fixed_df
    except Exception as e:
        logger.error(f"Failed to fix numeric regions: {e}")
        return df


def standardize_region_names(df: pd.DataFrame, region_col: str = None) -> pd.DataFrame:
    """
    Standardize region names using the mapping from config.

    Args:
        df: DataFrame to process
        region_col: Name of the region column (if None, use the first column)

    Returns:
        DataFrame with standardized region names
    """
    if df.empty:
        return df

    # If 'Region' column exists, use it; otherwise if region_col is not specified, use the first column
    if "Region" in df.columns:
        region_col = "Region"
    elif region_col is None:
        region_col = df.columns[0]

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Handle the case where 'nan' column exists but 'Region' doesn't
    if "nan" in df_copy.columns and region_col != "nan":
        # Check if nan column contains region names
        potential_regions = df_copy["nan"].dropna().astype(str).tolist()
        if any(
            region in " ".join(potential_regions)
            for region in ["TRREB", "TREB", "Toronto", "Halton", "Peel"]
        ):
            # Likely a region column - rename it to 'Region'
            df_copy = df_copy.rename(columns={"nan": "Region"})
            region_col = "Region"

    # Clean up region names - strip quotes, whitespace, etc.
    if pd.api.types.is_object_dtype(df_copy[region_col]):
        df_copy[region_col] = df_copy[region_col].astype(str).str.strip().str.strip('"')

    # Apply the mapping to the region column
    df_copy[region_col] = df_copy[region_col].apply(
        lambda x: REGION_NAME_MAPPING.get(x, x)
        if pd.notna(x) and not pd.api.types.is_numeric_dtype(pd.Series([x]))
        else x
    )

    # Handle numeric values that might be in the region column
    # This happens when CSV parsing goes wrong or columns are misaligned
    df_copy[region_col] = df_copy[region_col].apply(
        lambda x: None
        if pd.api.types.is_numeric_dtype(pd.Series([x])) and not isinstance(x, str)
        else x
    )

    return df_copy


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names using the mapping from config.

    Args:
        df: DataFrame to process

    Returns:
        DataFrame with standardized column names
    """
    if df.empty:
        return df

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Clean up column names by stripping whitespace and quotes
    df_copy.columns = [
        col.strip().strip('"').strip() if isinstance(col, str) else col
        for col in df_copy.columns
    ]

    # Handle common column name variations
    if "# of Sales" in df_copy.columns:
        df_copy = df_copy.rename(columns={"# of Sales": "Sales"})
    elif "Sales1" in df_copy.columns:
        df_copy = df_copy.rename(columns={"Sales1": "Sales"})

    # Create a new dictionary for columns that actually exist in the DataFrame
    column_mapping = {col: COLUMN_NAME_MAPPING.get(col, col) for col in df_copy.columns}

    # Rename the columns
    df_copy = df_copy.rename(columns=column_mapping)

    return df_copy


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert columns to appropriate numeric types.

    Args:
        df: DataFrame to process

    Returns:
        DataFrame with columns converted to appropriate types
    """
    if df.empty:
        return df

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Define column groups by type
    price_cols = ["Average Price", "Median Price", "Dollar Volume"]
    count_cols = ["Sales", "New Listings", "Active Listings"]
    percentage_cols = ["SNLR Trend", "Avg SP/LP"]
    decimal_cols = ["Months Inventory", "Avg DOM", "Avg PDOM"]

    # Process price columns (remove $ and ,)
    for col in price_cols:
        if col in df_copy.columns:
            try:
                if pd.api.types.is_object_dtype(df_copy[col]):
                    df_copy[col] = (
                        df_copy[col]
                        .astype(str)
                        .str.replace("$", "", regex=False)
                        .str.replace(",", "", regex=False)
                    )
                    # Convert to numeric
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")

                if pd.api.types.is_numeric_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].astype(int)
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")

    # Process count columns
    for col in count_cols:
        if col in df_copy.columns:
            try:
                if pd.api.types.is_object_dtype(df_copy[col]):
                    # Clean strings
                    df_copy[col] = df_copy[col].astype(str).str.strip().str.strip('"')
                    df_copy[col] = (
                        df_copy[col].astype(str).str.replace(",", "", regex=False)
                    )
                    # Convert to numeric
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").astype(
                        int
                    )
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")

    # Process percentage columns (remove %)
    for col in percentage_cols:
        if col in df_copy.columns:
            if pd.api.types.is_object_dtype(df_copy[col]):
                # Clean strings
                df_copy[col] = df_copy[col].astype(str).str.strip().str.strip('"')
                df_copy[col] = (
                    df_copy[col].astype(str).str.replace("%", "", regex=False)
                )
                # Convert to numeric
                df_copy[col] = (
                    pd.to_numeric(df_copy[col], errors="coerce") / 100
                ).round(4)

    # Process decimal columns
    for col in decimal_cols:
        if col in df_copy.columns:
            try:
                if pd.api.types.is_object_dtype(df_copy[col]):
                    # Clean strings first
                    df_copy[col] = df_copy[col].astype(str).str.strip().str.strip('"')
                    # Convert directly to numeric
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")

    return df_copy


def add_hierarchy_columns(df: pd.DataFrame, region_col: str = None) -> pd.DataFrame:
    """
    Add columns for parent regions to enable hierarchical analysis.

    Args:
        df: DataFrame to process
        region_col: Name of the region column (if None, use the first column)

    Returns:
        DataFrame with added hierarchy columns
    """
    if df.empty:
        return df

    # If region_col is not specified, use the first column
    if region_col is None:
        region_col = df.columns[0]

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Create a mapping from region to its parent
    region_to_parent = {}
    for parent, children in REGION_HIERARCHY.items():
        for child in children:
            region_to_parent[child] = parent

    # Add parent region column
    df_copy["parent_region"] = df_copy[region_col].apply(
        lambda x: region_to_parent.get(x, "None")
    )

    # Add region type column
    def get_region_type(region):
        if region == "TRREB Total":
            return "Total"
        elif region in REGION_HIERARCHY:
            return "Region"
        else:
            return "Municipality"

    df_copy["region_type"] = df_copy[region_col].apply(get_region_type)

    return df_copy


def add_date_components(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Add date component columns (year, month, quarter) for time series analysis.

    Args:
        df: DataFrame to process
        date_col: Name of the date column

    Returns:
        DataFrame with added date component columns
    """
    if df.empty or date_col not in df.columns:
        return df

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Convert date column to datetime if it's not already
    if not pd.api.types.is_datetime64_dtype(df_copy[date_col]):
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])

    # Add date components
    df_copy["year"] = df_copy[date_col].dt.year
    df_copy["month"] = df_copy[date_col].dt.month
    df_copy["quarter"] = df_copy[date_col].dt.quarter
    df_copy["month_name"] = df_copy[date_col].dt.strftime("%B")

    return df_copy


def determine_period(date_str: str) -> str:
    """
    Determine which period a date belongs to based on the format cutoff dates.

    Args:
        date_str: Date string in 'YYYY-MM' format

    Returns:
        'pre-2020', 'mid-period', or 'post-2022'
    """
    if date_str < EXTRACTION_CUTOFF_DATE:
        return "pre-2020"
    elif date_str < SECOND_FORMAT_CUTOFF_DATE:
        return "mid-period"
    else:
        return "post-2022"


def get_expected_columns(property_type: str, period: str) -> List[str]:
    """
    Get the expected columns for a given property type and period.

    Args:
        property_type: 'all_home_types' or 'detached'
        period: 'pre-2020', 'mid-period', or 'post-2022'

    Returns:
        List of expected column names
    """
    if property_type == "all_home_types":
        if period == "pre-2020":
            return PRE_2020_ALL_HOME_COLUMNS
        elif period == "mid-period":
            return MID_PERIOD_ALL_HOME_COLUMNS
        else:  # post-2022
            return POST_2022_ALL_HOME_COLUMNS
    else:  # detached
        if period == "pre-2020":
            return PRE_2020_DETACHED_COLUMNS
        elif period == "mid-period":
            return MID_PERIOD_DETACHED_COLUMNS
        else:  # post-2022
            return POST_2022_DETACHED_COLUMNS


def ensure_column_consistency(
    df: pd.DataFrame, expected_columns: List[str]
) -> pd.DataFrame:
    """
    Ensure the DataFrame has all expected columns in the right order.
    Missing columns are added with NaN values.

    Args:
        df: DataFrame to process
        expected_columns: List of expected column names

    Returns:
        DataFrame with consistent columns
    """
    if df.empty:
        return df

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Get the region column (first column)
    if len(df_copy.columns) > 0:
        region_col = df_copy.columns[0]
        # Sometimes the region column can be unnamed or have spaces
        if isinstance(region_col, str) and (
            region_col.strip() == "" or "Unnamed" in region_col
        ):
            # Try to identify a better region column
            for i, col in enumerate(df_copy.columns):
                # Check first few values to see if they look like region names
                sample_vals = df_copy[col].dropna().head(5).astype(str).tolist()
                if any(
                    region_name in sample_vals
                    for region_name in [
                        "TRREB Total",
                        "TREB Total",
                        "Halton",
                        "Peel",
                        "Toronto",
                    ]
                ):
                    region_col = col
                    break

            # If still using unnamed column but we have a proper region name column
            if "Unnamed" in region_col and "Region" in df_copy.columns:
                region_col = "Region"
    else:
        logger.warning("DataFrame has no columns for column consistency check")
        return df_copy

    # Check for missing expected columns and add them
    for col in expected_columns:
        if col not in df_copy.columns:
            logger.warning(f"Adding missing column: {col}")
            df_copy[col] = None

    # Merge the 'Region' and 'nan' columns if both exist (using Region as the primary)
    if "Region" in df_copy.columns and "nan" in df_copy.columns:
        # If Region column is empty but nan has values, use nan values
        mask = df_copy["Region"].isna() | (df_copy["Region"] == "")
        df_copy.loc[mask, "Region"] = df_copy.loc[mask, "nan"]
        # Drop the nan column
        df_copy = df_copy.drop(columns=["nan"])
        # Update region_col to be 'Region'
        region_col = "Region"

    # Create a new DataFrame with region column and expected columns in order
    # Start with the region column
    result_columns = ["Region"] if "Region" in df_copy.columns else [region_col]

    # Add all expected columns
    for col in expected_columns:
        if col in df_copy.columns and col != region_col and col != "Region":
            result_columns.append(col)

    # Add any additional columns that aren't in expected_columns
    for col in df_copy.columns:
        if col not in result_columns and col != region_col:
            # Skip any duplicate column variations
            skip_variations = False
            for existing_col in result_columns:
                if (
                    isinstance(col, str)
                    and isinstance(existing_col, str)
                    and col.replace(" ", "").replace(".", "").lower()
                    == existing_col.replace(" ", "").replace(".", "").lower()
                ):
                    skip_variations = True
                    break

            if not skip_variations:
                result_columns.append(col)

    # Make sure all result columns exist in df_copy
    valid_columns = [col for col in result_columns if col in df_copy.columns]

    # Return the DataFrame with reordered columns
    return df_copy[valid_columns]


def normalize_dataset(
    df: pd.DataFrame,
    date_str: Optional[str] = None,
    property_type: str = "all_home_types",
    date_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Apply all normalization steps to a dataset.

    Args:
        df: DataFrame to process
        date_str: Date string in 'YYYY-MM' format for determining period
        property_type: Type of property data ('all_home_types' or 'detached')
        date_col: Name of the date column (if available)

    Returns:
        Normalized DataFrame
    """
    if df.empty:
        return df

    # First, let's clean up potential CSV parsing issues
    # Strip quotes and whitespace from all string columns
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].astype(str).str.strip().str.strip('"')

    # Remove empty unnamed columns
    unnamed_cols = [col for col in df.columns if col.startswith("Unnamed:")]
    columns_to_drop = []
    for col in unnamed_cols:
        # Check if the column is empty or contains only NaN/empty strings
        if df[col].isna().all() or (df[col].astype(str).str.strip() == "").all():
            columns_to_drop.append(col)

    if columns_to_drop:
        logger.info(f"Dropping empty unnamed columns: {columns_to_drop}")
        df = df.drop(columns=columns_to_drop)

    # Handle 'nan' column which should be 'Region'
    if "nan" in df.columns and "Region" not in df.columns:
        # Rename the 'nan' column to 'Region'
        df = df.rename(columns={"nan": "Region"})
    elif "Unnamed: 0" in df.columns and "Region" not in df.columns:
        # Rename unnamed first column to 'Region'
        df = df.rename(columns={"Unnamed: 0": "Region"})

    # Check if the first column contains numeric values (indicates CSV parsing issue)
    # Attempt to fix the data structure if this is the case
    if pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
        df = fix_numeric_regions(df, date_str)

    # Try to standardize "All TRREB Areas" to "TRREB Total"
    if len(df.columns) > 0:
        if df.columns[0] == "Unnamed: 0" and any(
            df["Unnamed: 0"].astype(str).str.contains("TRREB Areas")
        ):
            df["Unnamed: 0"] = (
                df["Unnamed: 0"]
                .astype(str)
                .str.replace("All TRREB Areas", "TRREB Total")
            )

    # Remove any unnamed index columns if they exist
    if "Unnamed: 0" in df.columns:
        # Check if it's an index column by seeing if it contains region names
        if any(
            df["Unnamed: 0"].astype(str).str.contains("TRREB|TREB|Toronto|Halton|Peel")
        ):
            # Rename to a temporary name
            df = df.rename(columns={"Unnamed: 0": "Region"})
        else:
            # It's likely a true index column, drop it
            df = df.drop(columns=["Unnamed: 0"])

    # Determine period if date_str is provided
    period = None
    if date_str:
        period = determine_period(date_str)
        logger.info(
            f"Normalizing dataset for {date_str} - identified as {period} period"
        )
    else:
        logger.info(
            f"Normalizing dataset without specific date - applying general normalization"
        )

    # Apply each normalization step
    df = standardize_region_names(df)
    df = standardize_column_names(df)
    df = convert_numeric_columns(df)

    # Special handling for problematic files - check for completely numeric data
    # (likely a badly parsed CSV)
    if df.shape[1] > 0 and all(
        pd.api.types.is_numeric_dtype(df[col]) for col in df.columns
    ):
        logger.warning("DataFrame has all numeric columns - likely a parsing issue")
        if date_str and period:
            # Create a template with proper regions
            regions = [
                "TRREB Total",
                "Halton Region",
                "Burlington",
                "Halton Hills",
                "Milton",
                "Oakville",
                "Peel Region",
                "Brampton",
                "Caledon",
                "Mississauga",
                "City of Toronto",
            ]

            # Create appropriate column names based on period and property type
            columns = get_expected_columns(property_type, period)

            # Create a template dataframe with proper structure but empty values
            template_df = pd.DataFrame(
                index=range(len(regions)), columns=["Region"] + columns
            )
            template_df["Region"] = regions

            # Return the template with NaN values if we can't properly parse the data
            df = template_df

    df = add_hierarchy_columns(df)

    # Add date components if date_col is provided
    # if date_col is not None and date_col in df.columns:
    #     df = add_date_components(df, date_col)

    # Check and reorder columns based on expected format if period is known
    if period and property_type:
        expected_columns = get_expected_columns(property_type, period)
        df = ensure_column_consistency(df, expected_columns)

    return df
