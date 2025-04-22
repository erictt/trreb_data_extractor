"""
Integration of economic data with TRREB real estate data.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from trreb.config import PROCESSED_DIR, ECONOMIC_DIR
from trreb.services.economic.sources import get_all_data_sources
from trreb.utils.logging import logger


def load_economic_data(force_download: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Load all economic data sources.

    Args:
        force_download: Whether to force download even if cached data is available

    Returns:
        Dictionary of data source name to DataFrame
    """
    data_sources = get_all_data_sources()
    economic_data = {}

    for source in data_sources:
        try:
            logger.info(f"Loading data from {source.name}")
            df = source.get_data(force_download=force_download)
            if df is not None and not df.empty:
                economic_data[source.name] = df
                logger.info(f"Successfully loaded {len(df)} rows from {source.name}")
            else:
                logger.warning(f"No data loaded from {source.name}")
        except Exception as e:
            logger.error(f"Error loading data from {source.name}: {e}")

    return economic_data


def verify_data_format(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Verify and correct the data format to match expected CSV structure.

    Args:
        df: DataFrame to verify
        dataset_name: Name of the dataset for logging

    Returns:
        DataFrame with verified format
    """
    if df.empty:
        logger.warning(f"Empty DataFrame for {dataset_name}")
        return df

    # Check for required columns
    required_cols = ["year", "month", "date_str"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns in {dataset_name}: {missing_cols}")
        # Try to create missing columns if possible
        if "date_str" in df.columns and "year" not in df.columns:
            df["year"] = df["date_str"].str.split("-").str[0]
        if "date_str" in df.columns and "month" not in df.columns:
            df["month"] = df["date_str"].str.split("-").str[1]

    # Verify data types
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "month" in df.columns:
        df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")

    # Check for date_str format (YYYY-MM)
    if "date_str" in df.columns:
        invalid_format = ~df["date_str"].str.match(r"^\d{4}-\d{2}$")
        invalid_count = invalid_format.sum()
        if invalid_count > 0:
            logger.warning(
                f"Found {invalid_count} invalid date_str format in {dataset_name}"
            )
            # Try to fix if possible
            if "year" in df.columns and "month" in df.columns:
                mask = invalid_format
                df.loc[mask, "date_str"] = (
                    df.loc[mask, "year"].astype(str)
                    + "-"
                    + df.loc[mask, "month"].astype(str).str.zfill(2)
                )

    # Log verification results
    logger.info(
        f"Verified {dataset_name} format: {len(df)} rows, {', '.join(df.columns)} columns"
    )
    return df


def prepare_economic_data(force_download: bool = False) -> pd.DataFrame:
    """
    Prepare economic data for integration with TRREB data.
    This function can be run independently to download and prepare economic data
    even if TRREB data isn't available yet.

    Args:
        force_download: Whether to force download of economic data

    Returns:
        DataFrame containing the master economic dataset
    """
    # Load or create master economic dataset
    econ_path = ECONOMIC_DIR / "master_economic_data.csv"
    if econ_path.exists() and not force_download:
        try:
            logger.info(f"Loading existing economic data from {econ_path}")
            econ_df = pd.read_csv(econ_path)
            # Verify the format of the loaded data
            econ_df = verify_data_format(econ_df, "master_economic_data")
            
            # Check if the data includes 2015 records
            if "date_str" in econ_df.columns:
                if not any(econ_df["date_str"].str.startswith("2015")):
                    logger.info("Existing economic data doesn't include 2015 records. Forcing re-download.")
                    econ_df = create_master_economic_dataset()
        except Exception as e:
            logger.error(f"Error loading master economic data: {e}")
            econ_df = create_master_economic_dataset()
    else:
        # Force re-download of economic data
        if force_download:
            logger.info("Forcing download of economic data...")
        else:
            logger.info("No existing economic data found. Downloading...")
        econ_df = create_master_economic_dataset()

    return econ_df


def create_master_economic_dataset() -> pd.DataFrame:
    """
    Create a master dataset of all economic indicators.

    Returns:
        DataFrame containing all economic indicators
    """
    # Load all economic data
    logger.info("Creating master economic dataset from all sources...")
    economic_data = load_economic_data(force_download=True)  # Force download to get the latest data

    if not economic_data:
        logger.error("No economic data sources loaded. Please check API implementations.")
        return pd.DataFrame(columns=["year", "month", "date_str"])

    # Start with the first data source
    master_df = next(iter(economic_data.values())).copy()
    logger.info(f"Starting with {len(master_df)} rows from {next(iter(economic_data.keys()))}")

    # Merge with other data sources
    for name, df in economic_data.items():
        if df is master_df:
            continue

        # Check if 'date_str' column exists
        if "date_str" not in df.columns:
            logger.warning(f"'date_str' column not found in {name}, skipping")
            continue

        # Log the merge operation
        logger.info(f"Merging {name} data with {len(df)} rows")

        # Before merging, check for duplicate date_str values
        duplicates = df["date_str"].duplicated().sum()
        if duplicates > 0:
            logger.warning(f"Found {duplicates} duplicate date_str values in {name}")
            # Keep only the last occurrence of each date_str
            df = df.drop_duplicates(subset=["date_str"], keep="last")

        # Merge on 'date_str'
        before_rows = len(master_df)
        master_df = pd.merge(
            master_df, df, on="date_str", how="outer", suffixes=("", f"_{name}")
        )
        after_rows = len(master_df)

        logger.info(f"After merging {name}: {before_rows} rows -> {after_rows} rows")

    # Sort by date
    if "date_str" in master_df.columns:
        master_df = master_df.sort_values("date_str")

    # Ensure consistent data types across columns
    # Make sure we have the key columns: year, month, date_str
    if "year" in master_df.columns and "month" in master_df.columns:
        master_df["year"] = master_df["year"].astype("Int64")
        master_df["month"] = master_df["month"].astype("Int64")
    else:
        # If year/month columns are missing, create them from date_str
        try:
            master_df["year"] = (
                master_df["date_str"].str.split("-").str[0].astype("Int64")
            )
            master_df["month"] = (
                master_df["date_str"].str.split("-").str[1].astype("Int64")
            )
        except Exception as e:
            logger.error(f"Could not create year/month columns from date_str: {e}")

    # Check for and handle duplicate date_str in master dataset
    duplicates = master_df["date_str"].duplicated().sum()
    if duplicates > 0:
        logger.warning(
            f"Found {duplicates} duplicate date_str values in master dataset"
        )
        # Keep only the last occurrence of each date_str
        master_df = master_df.drop_duplicates(subset=["date_str"], keep="last")
    
    # If master dataset is empty after merging, log a clear error
    if master_df.empty:
        logger.error("Master economic dataset is empty! All data sources returned empty datasets.")
        logger.error("Please check the API implementations in the economic data sources.")
        # Return a minimal DataFrame with required columns
        return pd.DataFrame(columns=["year", "month", "date_str"])

    # Save the master dataset
    output_path = ECONOMIC_DIR / "master_economic_data.csv"
    master_df.to_csv(output_path, index=False)
    logger.info(f"Master economic dataset saved to {output_path}")

    # Log summary statistics for verification
    logger.info(f"Master economic dataset shape: {master_df.shape}")
    logger.info(
        f"Date range: {master_df['date_str'].min()} to {master_df['date_str'].max() if not master_df.empty else 'N/A'}"
    )
    logger.info(
        f"Number of indicators: {len(master_df.columns) - 3}"
    )  # -3 for date_str, year, month columns
    logger.info(f"Master economic data columns: {', '.join(master_df.columns)}")
    logger.info(f"Master economic data dtypes:\n{master_df.dtypes}")
    logger.info(
        f"Sample master economic data:\n{master_df.head(3) if not master_df.empty else 'Empty DataFrame'}"
    )

    return master_df


def integrate_economic_data(
    property_type: str,
    include_lags: bool = True,
    lag_periods: List[int] = [1, 3, 6, 12],
    force_download: bool = False,
) -> pd.DataFrame:
    """
    Integrate TRREB data with economic indicators.

    Args:
        property_type: Type of property (all_home_types or detached)
        include_lags: Whether to include lagged economic indicators
        lag_periods: List of lag periods to include
        force_download: Whether to force download of economic data

    Returns:
        DataFrame containing integrated TRREB and economic data
    """
    # Load normalized TRREB data
    trreb_path = PROCESSED_DIR / f"normalized_{property_type}.csv"

    # First, create economic data even if TRREB data doesn't exist yet
    # This allows users to download economic data separately
    econ_df = prepare_economic_data(force_download)

    if not trreb_path.exists():
        logger.warning(f"Normalized TRREB data not found at {trreb_path}")
        logger.info(
            f"Economic data has been downloaded and prepared, but no TRREB data to integrate."
        )
        logger.info(
            f"You can find the economic data at {ECONOMIC_DIR}/master_economic_data.csv"
        )
        return pd.DataFrame()

    trreb_df = pd.read_csv(trreb_path)
    # Try to parse as date and convert to YYYY-MM
    trreb_df["date_str"] = pd.to_datetime(trreb_df["date_str"]).dt.strftime("%Y-%m")

    # Get pre-prepared economic data (already handled at the beginning of the function)

    if econ_df.empty:
        logger.error("No economic data available. Please check data source implementations.")
        return trreb_df

    # Create lag features if requested
    if include_lags:
        # Identify numeric columns to lag
        numeric_cols = econ_df.select_dtypes(include=["number"]).columns
        logger.info(f"Creating lag features for {len(numeric_cols)} numeric columns")

        # For each lag period, create lagged features
        for lag in lag_periods:
            logger.info(f"Creating lag-{lag} features")
            # Create a copy of the economic data shifted by the lag period
            lag_df = econ_df.copy()

            # Sort by date_str to ensure correct lagging
            lag_df = lag_df.sort_values("date_str")

            # For each numeric column, create a lagged version
            for col in numeric_cols:
                if col in lag_df.columns and col != "date_str":
                    # Create the lagged feature name
                    lag_col = f"{col}_lag{lag}"

                    # Get the index position of the date_str column
                    try:
                        date_idx = lag_df.columns.get_loc("date_str")

                        # Create a new DataFrame with just the date_str and lagged column
                        temp_df = pd.DataFrame(
                            {
                                "date_str": lag_df["date_str"],
                                lag_col: lag_df[col].shift(lag),
                            }
                        )

                        # Merge back into the economic data
                        econ_df = pd.merge(econ_df, temp_df, on="date_str", how="left")
                    except Exception as e:
                        logger.error(f"Error creating lag feature {lag_col}: {e}")

    # Merge TRREB data with economic data
    logger.info(f"Merging TRREB {property_type} data with economic indicators")
    enriched_df = pd.merge(
        trreb_df, econ_df, on="date_str", how="left", suffixes=("", "_econ")
    )

    # Filter out duplicate columns
    cols_to_keep = [
        col
        for col in enriched_df.columns
        if not (
            col.endswith("_econ") and col.replace("_econ", "") in enriched_df.columns
        )
    ]
    enriched_df = enriched_df[cols_to_keep]
    logger.info(f"Final integrated dataset has {len(enriched_df)} rows and {len(enriched_df.columns)} columns")

    # Save the integrated dataset
    output_path = PROCESSED_DIR / f"integrated_economic_{property_type}.csv"
    enriched_df.to_csv(output_path, index=False)
    logger.info(f"Integrated economic data saved to {output_path}")

    return enriched_df


def integrate_economic_data_all(
    include_lags: bool = True,
    lag_periods: List[int] = [1, 3, 6, 12],
    force_download: bool = False,
) -> Dict[str, pd.DataFrame]:
    """
    Integrate all TRREB datasets with economic indicators.

    Args:
        include_lags: Whether to include lagged economic indicators
        lag_periods: List of lag periods to include
        force_download: Whether to force download of economic data

    Returns:
        Dictionary of property type to integrated DataFrame
    """
    property_types = ["all_home_types", "detached"]
    integrated_data = {}

    for property_type in property_types:
        try:
            logger.info(f"Integrating economic data with {property_type} property type")
            df = integrate_economic_data(
                property_type, include_lags, lag_periods, force_download
            )
            if not df.empty:
                integrated_data[property_type] = df
                logger.info(f"Successfully integrated {property_type} dataset with {len(df)} rows")
            else:
                logger.warning(f"No integrated data created for {property_type}")
        except Exception as e:
            logger.error(f"Error integrating {property_type} data: {e}")

    return integrated_data
