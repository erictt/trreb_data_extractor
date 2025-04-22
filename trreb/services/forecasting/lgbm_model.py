import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
from typing import Tuple, Optional, Dict, Any


def train_lgbm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: Optional[pd.DataFrame] = None,
    y_val: Optional[pd.Series] = None,
    lgbm_params: Optional[Dict[str, Any]] = None,
    early_stopping_rounds: Optional[int] = 50,
    verbose: int = -1,  # Default to silent for library use
) -> lgb.LGBMRegressor:
    """
    Trains a LightGBM Regressor model for direct time series forecasting.

    Args:
        X_train (pd.DataFrame): Training feature data.
        y_train (pd.Series): Training target data (should be the shifted target, e.g., y_{t+h}).
        X_val (Optional[pd.DataFrame]): Validation feature data for early stopping.
        y_val (Optional[pd.Series]): Validation target data for early stopping.
        lgbm_params (Optional[Dict[str, Any]]): Dictionary of parameters for LGBMRegressor.
                                                If None, uses default reasonable parameters.
        early_stopping_rounds (Optional[int]): Activates early stopping. Training stops if
                                               validation score doesn't improve after this many rounds.
                                               Requires X_val and y_val. Set to None to disable.
        verbose (int): Controls the verbosity of LightGBM training. Set to -1 for silent,
                       or higher values (e.g., 100) for periodic updates during training.

    Returns:
        lgb.LGBMRegressor: The trained LightGBM model object.
    """
    print("Starting LightGBM model training...")
    print(f"  Training features shape: {X_train.shape}")
    print(f"  Training target length: {len(y_train)}")

    if lgbm_params is None:
        # Default parameters - consider tuning these further
        lgbm_params = {
            "objective": "regression_l1",  # MAE loss, often good for price data
            "metric": "mae",
            "n_estimators": 1000,  # Start with a higher number, rely on early stopping
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 1,
            "lambda_l1": 0.1,
            "lambda_l2": 0.1,
            "num_leaves": 31,
            "verbose": -1,  # Controlled by the function's verbose param below
            "n_jobs": -1,  # Use all available CPU cores
            "seed": 42,  # For reproducibility
            "boosting_type": "gbdt",
        }
        print("Using default LightGBM parameters.")
    else:
        print(f"Using provided LightGBM parameters: {lgbm_params}")
        # Ensure verbosity parameter is respected
        lgbm_params["verbose"] = -1 if verbose <= 0 else verbose

    model = lgb.LGBMRegressor(**lgbm_params)

    fit_params = {}
    eval_metric = lgbm_params.get("metric", "mae")  # Get metric for callback name

    if early_stopping_rounds is not None and X_val is not None and y_val is not None:
        print(
            f"  Using early stopping with {early_stopping_rounds} rounds (metric: {eval_metric})."
        )
        print(f"  Validation features shape: {X_val.shape}")
        print(f"  Validation target length: {len(y_val)}")

        # Ensure index alignment for validation set
        if not X_val.index.equals(y_val.index):
            raise ValueError("Index of X_val and y_val must match.")

        fit_params["eval_set"] = [(X_val, y_val)]
        # Note: LightGBM 3.x+ uses callbacks for early stopping
        fit_params["callbacks"] = [
            lgb.early_stopping(
                stopping_rounds=early_stopping_rounds, verbose=(verbose > 0)
            ),
            lgb.log_evaluation(
                period=verbose if verbose > 0 else 0
            ),  # Log evaluation based on verbose level
        ]

    else:
        print(
            "  Early stopping not enabled (requires X_val, y_val, and early_stopping_rounds > 0)."
        )
        fit_params["callbacks"] = [
            lgb.log_evaluation(period=verbose if verbose > 0 else 0)
        ]

    try:
        print(f"Fitting model...")
        model.fit(
            X_train,
            y_train,
            eval_set=fit_params.get("eval_set"),
            callbacks=fit_params.get("callbacks"),
        )
        print("\nLightGBM training complete.")
        if (
            "callbacks" in fit_params
            and lgb.early_stopping in [type(cb) for cb in fit_params["callbacks"]]
            and hasattr(model, "best_iteration_")
            and model.best_iteration_
        ):
            print(f"  Best iteration found: {model.best_iteration_}")

    except Exception as e:
        print(f"Error during LightGBM fitting: {e}")
        import traceback

        traceback.print_exc()
        raise

    return model


def predict_lgbm(model: lgb.LGBMRegressor, X_future: pd.DataFrame) -> pd.Series:
    """
    Generates forecasts using a trained LightGBM model.

    Args:
        model (lgb.LGBMRegressor): The trained LightGBM model object.
        X_future (pd.DataFrame): Feature data for the period to forecast.
                                 Must have the same columns as the training data.

    Returns:
        pd.Series: A Series containing the forecasts, indexed like X_future.
    """
    print(f"Generating LightGBM forecast for {len(X_future)} steps...")
    try:
        predictions = model.predict(X_future)
        # Create a pandas Series with the same index as X_future
        predictions_series = pd.Series(
            predictions, index=X_future.index, name="Predicted"
        )
        print("Forecast generation complete.")
        return predictions_series
    except Exception as e:
        print(f"Error during LightGBM prediction: {e}")
        import traceback

        traceback.print_exc()
        raise
