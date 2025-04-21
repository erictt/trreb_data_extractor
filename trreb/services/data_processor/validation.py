"""
Data validation utilities for TRREB data.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Union

from trreb.config import (
    ALL_REGIONS,
    PRE_2020_ALL_HOME_COLUMNS,
    PRE_2020_DETACHED_COLUMNS,
    MID_PERIOD_ALL_HOME_COLUMNS,
    MID_PERIOD_DETACHED_COLUMNS,
    POST_2022_ALL_HOME_COLUMNS,
    POST_2022_DETACHED_COLUMNS
)
from trreb.services.data_processor.normalization import determine_period, get_expected_columns


class ValidationResult:
    """Class to hold validation results."""

    def __init__(self, is_valid: bool = True):
        """
        Initialize a validation result.

        Args:
            is_valid: Whether the data is valid
        """
        self.is_valid = is_valid
        self.issues = []

    def add_issue(self, issue: str):
        """
        Add an issue to the validation result.

        Args:
            issue: Description of the issue
        """
        self.is_valid = False
        self.issues.append(issue)

    def get_issues_str(self) -> str:
        """
        Get a string representation of all issues.

        Returns:
            String representation of all issues
        """
        if not self.issues:
            return "No validation issues found."

        return "\n".join([f"- {issue}" for issue in self.issues])

    def __str__(self) -> str:
        """
        Get a string representation of the validation result.

        Returns:
            String representation of the validation result
        """
        if self.is_valid:
            return "Validation passed: No issues found."
        else:
            return f"Validation failed with {len(self.issues)} issues:\n{self.get_issues_str()}"


def validate_regions(df: pd.DataFrame, region_col: str = None) -> ValidationResult:
    """
    Validate region names against the known regions list.

    Args:
        df: DataFrame to validate
        region_col: Name of the region column (if None, use the first column)

    Returns:
        ValidationResult containing any issues
    """
    result = ValidationResult()

    # If region_col is not specified, use the first column
    if region_col is None:
        region_col = df.columns[0]

    # Check that region_col exists
    if region_col not in df.columns:
        result.add_issue(f"Region column '{region_col}' not found in DataFrame.")
        return result

    # Check for unknown regions
    regions = df[region_col].unique()
    # Convert non-string regions to strings and filter out NaN values
    unknown_regions = []
    for r in regions:
        if pd.notna(r) and r not in ALL_REGIONS:
            # Convert to string if it's not already
            if not isinstance(r, str):
                r_str = str(r)
            else:
                r_str = r
            unknown_regions.append(r_str)

    if unknown_regions:
        result.add_issue(
            f"Unknown regions found: {', '.join(unknown_regions)}. "
            f"These may need to be added to the standardization mapping."
        )

    # Check for missing key regions
    missing_key_regions = []
    for region in ["TRREB Total", "Halton Region", "Peel Region", "City of Toronto"]:
        if region not in regions:
            missing_key_regions.append(region)

    if missing_key_regions:
        result.add_issue(
            f"Missing key regions: {', '.join(missing_key_regions)}. "
            f"This may indicate incomplete data."
        )

    # Check that the number of regions is reasonable
    min_expected_regions = (
        15  # A very minimal TRREB report would have at least 15 regions
    )
    if len(regions) < min_expected_regions:
        result.add_issue(
            f"Only {len(regions)} regions found. Expected at least {min_expected_regions}. "
            f"This may indicate data extraction issues."
        )

    return result


def validate_numeric_columns(
    df: pd.DataFrame, expected_columns: Optional[List[str]] = None,
    date_str: Optional[str] = None, property_type: Optional[str] = None
) -> ValidationResult:
    """
    Validate numeric columns for missing values, outliers, etc.

    Args:
        df: DataFrame to validate
        expected_columns: List of columns that should be numeric (if None, use a default list)
        date_str: Date string in 'YYYY-MM' format for determining period
        property_type: Type of property data ('all_home_types' or 'detached')

    Returns:
        ValidationResult containing any issues
    """
    result = ValidationResult()

    # Default numeric columns if not specified
    if expected_columns is None:
        if date_str and property_type:
            # Determine the period and get expected columns
            period = determine_period(date_str)
            expected_columns = get_expected_columns(property_type, period)
        else:
            # Use a comprehensive list if period can't be determined
            expected_columns = [
                "Sales",
                "Dollar Volume",
                "Average Price",
                "Median Price",
                "New Listings",
                "Active Listings",
                "Months Inventory",
                "Avg SP/LP",
                "Avg DOM",
                "Avg PDOM",
            ]

    # Filter to only columns that exist in the DataFrame
    numeric_cols = [col for col in expected_columns if col in df.columns]

    if not numeric_cols:
        result.add_issue(
            f"None of the expected numeric columns found: {', '.join(expected_columns)}. "
            f"This may indicate column naming issues."
        )
        return result

    # Check for non-numeric values
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            result.add_issue(
                f"Column '{col}' is not numeric. "
                f"This may indicate parsing or conversion issues."
            )

    # Check for missing values
    for col in numeric_cols:
        missing_count = df[col].isna().sum()
        missing_pct = missing_count / len(df) * 100
        # Only flag if more than 5% missing (to account for period differences)
        if missing_pct > 5:
            result.add_issue(
                f"Column '{col}' has {missing_count} missing values ({missing_pct:.1f}%). "
                f"Consider imputation or filtering strategies."
            )

    # Check for negative values in non-percentage columns
    for col in [c for c in numeric_cols if c not in ["Avg SP/LP"]]:
        if pd.api.types.is_numeric_dtype(df[col]):
            neg_count = (df[col] < 0).sum()
            # Only flag if more than a few rows are affected
            if neg_count > 3:
                result.add_issue(
                    f"Column '{col}' has {neg_count} negative values. "
                    f"This may indicate data quality issues."
                )

    # Check for outliers using IQR method - only for non-date-sensitive columns
    # Columns like price and volume will naturally vary over time periods
    robust_cols = ["Avg SP/LP", "Avg DOM", "Avg PDOM", "SNLR Trend", "Months Inventory"]
    for col in [c for c in numeric_cols if c in robust_cols]:
        if pd.api.types.is_numeric_dtype(df[col]) and not df[col].isna().all():
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            # Use a more generous threshold for outliers (5 instead of 3)
            lower_bound = Q1 - 5 * IQR
            upper_bound = Q3 + 5 * IQR

            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if len(outliers) > 5:  # Only report if significant number of outliers
                result.add_issue(
                    f"Column '{col}' has {len(outliers)} outliers. "
                    f"This may require further investigation."
                )

    return result


def validate_data_consistency(df: pd.DataFrame) -> ValidationResult:
    """
    Validate internal data consistency (e.g., Average Price calculation).

    Args:
        df: DataFrame to validate

    Returns:
        ValidationResult containing any issues
    """
    result = ValidationResult()

    # Check that all required columns exist
    required_cols = ["Sales", "Dollar Volume", "Average Price"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        result.add_issue(
            f"Missing required columns for consistency check: {', '.join(missing_cols)}. "
            f"Skipping consistency validation."
        )
        return result

    # Check Average Price calculation (Dollar Volume / Sales)
    # Allow for some floating-point imprecision by using a tolerance
    if (
        pd.api.types.is_numeric_dtype(df["Sales"])
        and pd.api.types.is_numeric_dtype(df["Dollar Volume"])
        and pd.api.types.is_numeric_dtype(df["Average Price"])
    ):
        # Calculate the expected average price
        expected_avg_price = df["Dollar Volume"] / df["Sales"]

        # Compare with a reasonable tolerance (0.5% difference)
        tolerance = 0.005

        # Identify rows with inconsistent average price
        inconsistent_rows = df[
            (
                ~np.isclose(
                    df["Average Price"],
                    expected_avg_price,
                    rtol=tolerance,
                    equal_nan=True,
                )
            )
            & (~df["Average Price"].isna())
            & (~expected_avg_price.isna())
        ]

        if len(inconsistent_rows) > 0:
            result.add_issue(
                f"Found {len(inconsistent_rows)} rows with inconsistent Average Price calculation. "
                f"This may indicate data quality issues or calculation differences."
            )

    # Check SNLR calculation if columns are available
    if (
        "SNLR Trend" in df.columns
        and "Sales" in df.columns
        and "New Listings" in df.columns
    ):
        if (
            pd.api.types.is_numeric_dtype(df["SNLR Trend"])
            and pd.api.types.is_numeric_dtype(df["Sales"])
            and pd.api.types.is_numeric_dtype(df["New Listings"])
        ):
            # SNLR is typically Sales / New Listings, but the trend may use a moving average
            # So we just check if it's in a reasonable range
            invalid_snlr = df[(df["SNLR Trend"] < 0) | (df["SNLR Trend"] > 1.5)]

            if len(invalid_snlr) > 0:
                result.add_issue(
                    f"Found {len(invalid_snlr)} rows with invalid SNLR Trend values "
                    f"(outside range [0, 1.5]). This may indicate data quality issues."
                )

    return result


def validate_time_series_continuity(
    df: pd.DataFrame, date_col: str, region_col: str = None
) -> ValidationResult:
    """
    Validate time series continuity (e.g., no missing months).

    Args:
        df: DataFrame to validate
        date_col: Name of the date column
        region_col: Name of the region column (if None, use the first column)

    Returns:
        ValidationResult containing any issues
    """
    result = ValidationResult()

    # Check that required columns exist
    if date_col not in df.columns:
        result.add_issue(f"Date column '{date_col}' not found in DataFrame.")
        return result

    # If region_col is not specified, use the first column
    if region_col is None:
        region_col = df.columns[0]

    if region_col not in df.columns:
        result.add_issue(f"Region column '{region_col}' not found in DataFrame.")
        return result

    # Convert date column to datetime if it's not already
    if not pd.api.types.is_datetime64_dtype(df[date_col]):
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col])
        except Exception as e:
            result.add_issue(f"Failed to convert '{date_col}' to datetime: {e}")
            return result

    # Check for each major region
    for region in ["TRREB Total", "Halton Region", "Peel Region", "City of Toronto"]:
        region_data = df[df[region_col] == region]

        if len(region_data) == 0:
            continue  # Skip if region not found

        # Sort by date
        region_data = region_data.sort_values(date_col)

        # Check for continuous months
        date_series = region_data[date_col]
        date_diffs = date_series.diff().dropna()

        # Check for gaps in the time series
        # We'll consider a gap as anything more than 35 days (to account for month length variations)
        gaps = date_diffs[date_diffs.dt.days > 35]

        if len(gaps) > 0:
            gap_dates = date_series[gaps.index].dt.strftime("%Y-%m")
            result.add_issue(
                f"Found {len(gaps)} gaps in time series for {region}. "
                f"Missing months around: {', '.join(gap_dates)}. "
                f"This may indicate missing data."
            )

    return result


def generate_validation_report(
    df: pd.DataFrame, date_col: Optional[str] = None,
    date_str: Optional[str] = None, property_type: Optional[str] = None
) -> ValidationResult:
    """
    Generate a comprehensive validation report for a DataFrame.

    Args:
        df: DataFrame to validate
        date_col: Name of the date column (if available)
        date_str: Date string in 'YYYY-MM' format for determining period
        property_type: Type of property data ('all_home_types' or 'detached')

    Returns:
        ValidationResult containing any issues
    """
    # Combine validation results from all checks
    result = ValidationResult()

    # Run each validation check
    region_validation = validate_regions(df)
    numeric_validation = validate_numeric_columns(df, None, date_str, property_type)
    consistency_validation = validate_data_consistency(df)

    # Combine issues from all validations
    for validation in [region_validation, numeric_validation, consistency_validation]:
        for issue in validation.issues:
            result.add_issue(issue)

    # Run time series validation if date_col is provided
    if date_col is not None and date_col in df.columns:
        time_series_validation = validate_time_series_continuity(df, date_col)
        for issue in time_series_validation.issues:
            result.add_issue(issue)

    # Additional validation: Check for expected columns based on period
    if date_str and property_type:
        period = determine_period(date_str)
        expected_columns = get_expected_columns(property_type, period)
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols:
            result.add_issue(
                f"Missing expected columns for {period} {property_type}: {', '.join(missing_cols)}"
            )

    return result
