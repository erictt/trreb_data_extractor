"""
Data normalization utilities for TRREB data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union

from trreb.config import COLUMN_NAME_MAPPING, REGION_HIERARCHY, REGION_NAME_MAPPING, ALL_REGIONS
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
                df_copy[col] = df_copy[col].astype(str).str.replace("$", "", regex=False)
                df_copy[col] = df_copy[col].astype(str).str.replace(",", "", regex=False)
                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")
    
    # Process count columns
    for col in count_cols:
        if col in df_copy.columns:
            try:
                if df_copy[col].dtype == object:  # Only process if it's a string/object
                    df_copy[col] = df_copy[col].astype(str).str.replace(",", "", regex=False)
                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")
    
    # Process percentage columns (remove %)
    for col in percentage_cols:
        if col in df_copy.columns:
            try:
                df_copy[col] = df_copy[col].astype(str).str.replace("%", "", regex=False)
                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
                # Convert to decimal (e.g., 95% -> 0.95)
                df_copy[col] = df_copy[col] / 100
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")
    
    # Process decimal columns
    for col in decimal_cols:
        if col in df_copy.columns:
            try:
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


def normalize_dataset(df: pd.DataFrame, date_col: Optional[str] = None) -> pd.DataFrame:
    """
    Apply all normalization steps to a dataset.
    
    Args:
        df: DataFrame to process
        date_col: Name of the date column (if available)
        
    Returns:
        Normalized DataFrame
    """
    if df.empty:
        return df
    
    # Apply each normalization step
    df = standardize_region_names(df)
    df = standardize_column_names(df)
    df = convert_numeric_columns(df)
    df = add_hierarchy_columns(df)
    
    # Add date components if date_col is provided
    if date_col is not None and date_col in df.columns:
        df = add_date_components(df, date_col)
    
    return df
