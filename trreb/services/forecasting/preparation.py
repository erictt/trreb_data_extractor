import pandas as pd
from typing import List, Optional


def prepare_forecasting_data(
    input_path: str,
    region_filter: str = "TRREB Total",
    target_variable: str = "Median Price",
    forecast_horizon: int = 6,
    feature_cols: Optional[List[str]] = None,
    lag_cols: Optional[List[str]] = None,
    lag_periods: Optional[List[int]] = None,
    date_col: str = "date_str",
    region_col: str = "Region",
) -> pd.DataFrame:
    """
    Prepares the integrated housing and economic data for time series forecasting.

    Args:
        input_path (str): Path to the integrated CSV file (should be determined
                          by calling script using project's path management).
        region_filter (str): The specific region to filter the data for (e.g., 'TRREB Total').
        target_variable (str): The name of the column to be forecasted.
        forecast_horizon (int): The number of steps ahead to forecast (e.g., 6 for 6 months).
                                Used to create the shifted target variable for direct forecasting.
        feature_cols (Optional[List[str]]): List of initial feature columns to keep.
                                            If None, uses a default set.
        lag_cols (Optional[List[str]]): List of columns to create lagged features for.
                                        If None, uses a default set including the target variable.
        lag_periods (Optional[List[int]]): List of lag periods (in months) to create.
                                           If None, uses [1, 3, 6, 12].
        date_col (str): Name of the column containing date strings.
        region_col (str): Name of the column containing region names.

    Returns:
        pd.DataFrame: A DataFrame preprocessed and ready for splitting and modeling.
                      Includes original features, lagged features, and the shifted target
                      variable ('target_variable_t_plus_h'). Rows with NaNs introduced
                      by lagging/shifting are dropped.
    """
    print(f"Loading data from: {input_path}")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: File not found at {input_path}")
        raise
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

    # --- Basic Filtering and Date Handling ---
    print(f"Filtering data for region: {region_filter}")
    df = df[df[region_col] == region_filter].copy()

    if df.empty:
        raise ValueError(
            f"No data found for region '{region_filter}'. Check region name."
        )

    print(f"Converting '{date_col}' to datetime and setting as index.")
    try:
        # Assuming date_str is in 'YYYY-MM' format
        df[date_col] = pd.to_datetime(df[date_col] + "-01")
    except Exception as e:
        print(f"Error converting date column: {e}. Ensure format is like 'YYYY-MM'.")
        raise

    df = df.set_index(date_col)
    df = df.sort_index()  # Ensure chronological order

    # --- Feature Selection ---
    if feature_cols is None:
        # Default features: target, key housing metrics, current & lagged rates
        feature_cols = [
            target_variable,
            "Sales",
            "New Listings",
            "Active Listings",
            "overnight_rate",
            "prime_rate",
            "mortgage_5yr_rate",
            "overnight_rate_lag12",
            "prime_rate_lag12",
            "mortgage_5yr_rate_lag12",
        ]
        # Ensure target is included if not explicitly mentioned
        if target_variable not in feature_cols:
            feature_cols.insert(0, target_variable)
        # Ensure all default cols exist in the DataFrame
        feature_cols = [col for col in feature_cols if col in df.columns]
        print(f"Using default feature columns: {feature_cols}")
    else:
        # Ensure target variable is included
        if target_variable not in feature_cols:
            feature_cols.insert(0, target_variable)
        # Check if all specified columns exist
        missing_cols = [col for col in feature_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Specified feature columns not found in DataFrame: {missing_cols}"
            )
        print(f"Using specified feature columns: {feature_cols}")

    # Select only the necessary columns early to reduce memory usage
    df_processed = df[feature_cols].copy()

    # --- Lag Feature Creation ---
    if lag_cols is None:
        # Default columns to lag: target and key housing metrics
        lag_cols = [target_variable, "Sales", "New Listings", "Active Listings"]
        # Filter default lag_cols to only those present in df_processed
        lag_cols = [col for col in lag_cols if col in df_processed.columns]
        print(f"Creating lags for default columns: {lag_cols}")
    else:
        # Check if specified lag columns exist
        missing_lag_cols = [col for col in lag_cols if col not in df_processed.columns]
        if missing_lag_cols:
            raise ValueError(
                f"Specified lag columns not found in DataFrame: {missing_lag_cols}"
            )
        print(f"Creating lags for specified columns: {lag_cols}")

    if lag_periods is None:
        lag_periods = [1, 3, 6, 12]
        print(f"Using default lag periods: {lag_periods}")
    else:
        print(f"Using specified lag periods: {lag_periods}")

    print("Creating lag features...")
    for col in lag_cols:
        for lag in lag_periods:
            lag_col_name = f"{col}_lag_{lag}"
            df_processed[lag_col_name] = df_processed[col].shift(lag)

    # --- Target Variable Creation (for Direct Forecasting) ---
    target_col_name = f"{target_variable}_t_plus_{forecast_horizon}"
    print(
        f"Creating target variable '{target_col_name}' by shifting '{target_variable}' by -{forecast_horizon}"
    )
    df_processed[target_col_name] = df_processed[target_variable].shift(
        -forecast_horizon
    )

    # --- Handle NaNs ---
    initial_rows = len(df_processed)
    df_processed = df_processed.dropna()
    final_rows = len(df_processed)
    print(
        f"Dropped {initial_rows - final_rows} rows containing NaNs (due to lags/shifting)."
    )

    if df_processed.empty:
        print(
            "Warning: DataFrame is empty after dropping NaNs. Check lag periods and forecast horizon."
        )

    print(f"Preprocessing complete. Final DataFrame shape: {df_processed.shape}")
    return df_processed
