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
    SECOND_FORMAT_CUTOFF_DATE
)
from trreb.utils.logging import logger


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

    # If region_col is not specified, use the first column
    if region_col is None:
        region_col = df.columns[0]

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Apply the mapping to the region column
    df_copy[region_col] = df_copy[region_col].apply(
        lambda x: REGION_NAME_MAPPING.get(x, x) if pd.notna(x) else x
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
                    # Clean strings
                    df_copy[col] = df_copy[col].astype(str).str.replace("$", "", regex=False)
                    df_copy[col] = df_copy[col].astype(str).str.replace(",", "", regex=False)
                    # Convert to numeric
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")

    # Process count columns
    for col in count_cols:
        if col in df_copy.columns:
            try:
                if pd.api.types.is_object_dtype(df_copy[col]):
                    # Clean strings
                    df_copy[col] = df_copy[col].astype(str).str.replace(",", "", regex=False)
                    # Convert to numeric
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")

    # Process percentage columns (remove %)
    for col in percentage_cols:
        if col in df_copy.columns:
            try:
                if pd.api.types.is_object_dtype(df_copy[col]):
                    # Clean strings
                    df_copy[col] = df_copy[col].astype(str).str.replace("%", "", regex=False)
                    # Convert to numeric
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
                    # Convert to decimal (e.g., 95% -> 0.95)
                    df_copy[col] = df_copy[col] / 100
                elif pd.api.types.is_numeric_dtype(df_copy[col]):
                    # If already numeric, check if needs to be divided by 100
                    if df_copy[col].max() > 1.5 and df_copy[col].min() >= 0:
                        # Likely a percentage value (e.g., 95 instead of 0.95)
                        df_copy[col] = df_copy[col] / 100
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")

    # Process decimal columns
    for col in decimal_cols:
        if col in df_copy.columns:
            try:
                if pd.api.types.is_object_dtype(df_copy[col]):
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
        return 'pre-2020'
    elif date_str < SECOND_FORMAT_CUTOFF_DATE:
        return 'mid-period'
    else:
        return 'post-2022'

def get_expected_columns(property_type: str, period: str) -> List[str]:
    """
    Get the expected columns for a given property type and period.
    
    Args:
        property_type: 'all_home_types' or 'detached'
        period: 'pre-2020', 'mid-period', or 'post-2022'
        
    Returns:
        List of expected column names
    """
    if property_type == 'all_home_types':
        if period == 'pre-2020':
            return PRE_2020_ALL_HOME_COLUMNS
        elif period == 'mid-period':
            return MID_PERIOD_ALL_HOME_COLUMNS
        else:  # post-2022
            return POST_2022_ALL_HOME_COLUMNS
    else:  # detached
        if period == 'pre-2020':
            return PRE_2020_DETACHED_COLUMNS
        elif period == 'mid-period':
            return MID_PERIOD_DETACHED_COLUMNS
        else:  # post-2022
            return POST_2022_DETACHED_COLUMNS

def ensure_column_consistency(df: pd.DataFrame, expected_columns: List[str]) -> pd.DataFrame:
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
    else:
        logger.warning("DataFrame has no columns for column consistency check")
        return df_copy
    
    # Check for missing expected columns and add them
    for col in expected_columns:
        if col not in df_copy.columns:
            logger.warning(f"Adding missing column: {col}")
            df_copy[col] = None
    
    # Create a new DataFrame with region column and expected columns in order
    # Start with the region column
    result_columns = [region_col]
    
    # Add all expected columns
    for col in expected_columns:
        if col in df_copy.columns and col != region_col:
            result_columns.append(col)
    
    # Add any additional columns that aren't in expected_columns
    for col in df_copy.columns:
        if col not in result_columns and col != region_col:
            result_columns.append(col)
    
    # Return the DataFrame with reordered columns
    return df_copy[result_columns]

def normalize_dataset(
    df: pd.DataFrame, 
    date_str: Optional[str] = None, 
    property_type: str = 'all_home_types', 
    date_col: Optional[str] = None
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
        
    # Determine period if date_str is provided
    period = None
    if date_str:
        period = determine_period(date_str)
        logger.info(f"Normalizing dataset for {date_str} - identified as {period} period")
    else:
        logger.info(f"Normalizing dataset without specific date - applying general normalization")

    # Apply each normalization step
    df = standardize_region_names(df)
    df = standardize_column_names(df)
    df = convert_numeric_columns(df)
    df = add_hierarchy_columns(df)

    # Add date components if date_col is provided
    if date_col is not None and date_col in df.columns:
        df = add_date_components(df, date_col)
        
    # Check and reorder columns based on expected format if period is known
    if period and property_type:
        expected_columns = get_expected_columns(property_type, period)
        df = ensure_column_consistency(df, expected_columns)

    return df
