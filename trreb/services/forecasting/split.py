import pandas as pd
from typing import Tuple, Optional


def split_data_chronological(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.15,
    validation_size: Optional[float] = 0.15,
) -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.Series],
    Optional[pd.Series],
]:
    """
    Splits time series data chronologically into training, validation, and test sets.

    Args:
        df (pd.DataFrame): The prepared DataFrame with features and the target column.
                           Must have a DatetimeIndex sorted chronologically.
        target_col (str): The name of the target variable column.
        test_size (float): The proportion of the data to use for the test set (e.g., 0.15 for 15%).
        validation_size (Optional[float]): The proportion of the data to use for the validation set.
                                           If None, only train and test sets are returned.
                                           Defaults to 0.15 (15%).

    Returns:
        Tuple: Depending on validation_size:
            - If validation_size is not None:
                (X_train, X_val, X_test, y_train, y_val, y_test)
            - If validation_size is None:
                (X_train, X_test, y_train, y_test)

        Where:
            X_train, X_val, X_test are feature DataFrames.
            y_train, y_val, y_test are target Series.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be a DatetimeIndex.")
    if not df.index.is_monotonic_increasing:
        raise ValueError("DataFrame index must be sorted chronologically.")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    n = len(df)
    n_test = int(n * test_size)
    if n_test == 0 and test_size > 0:
        print(
            f"Warning: Test set size is zero with test_size={test_size} and n={n}. Adjust size or check data."
        )
        n_test = 1 if n > 0 else 0  # Ensure at least 1 sample if possible

    if validation_size is not None:
        n_val = int(n * validation_size)
        if n_val == 0 and validation_size > 0:
            print(
                f"Warning: Validation set size is zero with validation_size={validation_size} and n={n}. Adjust size or check data."
            )
            n_val = 1 if n > n_test else 0  # Ensure at least 1 sample if possible

        n_train = n - n_test - n_val
        if n_train <= 0:
            raise ValueError(
                "Not enough data for train/validation/test split with the given sizes."
            )

        print(f"Splitting data: n={n}")
        print(f"  Train size: {n_train} ({n_train / n:.1%})")
        print(f"  Validation size: {n_val} ({n_val / n:.1%})")
        print(f"  Test size: {n_test} ({n_test / n:.1%})")

        # Split data
        train_df = df.iloc[:n_train]
        val_df = df.iloc[n_train : n_train + n_val]
        test_df = df.iloc[n_train + n_val :]

        # Separate features (X) and target (y)
        y_train = train_df[target_col]
        X_train = train_df.drop(columns=[target_col])

        y_val = val_df[target_col]
        X_val = val_df.drop(columns=[target_col])

        y_test = test_df[target_col]
        X_test = test_df.drop(columns=[target_col])

        print("Split complete (Train, Validation, Test).")
        return X_train, X_val, X_test, y_train, y_val, y_test

    else:
        # Only train/test split
        n_train = n - n_test
        if n_train <= 0:
            raise ValueError(
                "Not enough data for train/test split with the given test_size."
            )

        print(f"Splitting data: n={n}")
        print(f"  Train size: {n_train} ({n_train / n:.1%})")
        print(f"  Test size: {n_test} ({n_test / n:.1%})")

        # Split data
        train_df = df.iloc[:n_train]
        test_df = df.iloc[n_train:]

        # Separate features (X) and target (y)
        y_train = train_df[target_col]
        X_train = train_df.drop(columns=[target_col])

        y_test = test_df[target_col]
        X_test = test_df.drop(columns=[target_col])

        print("Split complete (Train, Test).")
        return X_train, X_test, y_train, y_test
