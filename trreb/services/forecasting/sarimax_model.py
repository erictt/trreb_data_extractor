import pandas as pd
import pmdarima as pm
from pmdarima import model_selection
from typing import Tuple, Optional


def train_sarimax(
    y_train: pd.Series,
    exog_train: Optional[pd.DataFrame] = None,
    seasonal: bool = True,
    m: int = 12,
    **kwargs,
) -> pm.arima.ARIMA:
    """
    Trains a SARIMAX model using pmdarima's auto_arima for order selection.

    Args:
        y_train (pd.Series): The target variable training data (endogenous).
                             Should be the *original* target series for the training period.
        exog_train (Optional[pd.DataFrame]): Exogenous variables for training.
                                              Should align with y_train index.
        seasonal (bool): Whether to fit a seasonal model. Defaults to True.
        m (int): The period for seasonal differencing. Defaults to 12 for monthly data.
        **kwargs: Additional arguments passed directly to pmdarima.auto_arima
                  (e.g., start_p, max_p, stepwise, trace, error_action, etc.).

    Returns:
        pmdarima.arima.ARIMA: The fitted auto_arima model object.
    """
    print("Starting SARIMAX model training with auto_arima...")
    print(f"  Target variable length: {len(y_train)}")
    if exog_train is not None:
        print(f"  Exogenous variables shape: {exog_train.shape}")
        # Ensure index alignment
        if not y_train.index.equals(exog_train.index):
            raise ValueError("Index of y_train and exog_train must match.")

    # Default auto_arima settings (can be overridden by kwargs)
    auto_arima_defaults = {
        "seasonal": seasonal,
        "m": m,
        "stepwise": True,  # Use stepwise algorithm for faster search
        "suppress_warnings": True,  # Suppress convergence warnings
        "error_action": "ignore",  # Skip models that fail to fit
        "trace": False,  # Default to less verbose for library use
        "n_jobs": -1,  # Use all available CPU cores
    }
    # Allow kwargs to override defaults, including 'trace'
    auto_arima_defaults.update(kwargs)

    try:
        model = pm.auto_arima(
            y=y_train,
            X=exog_train,  # pmdarima uses 'X' for exogenous
            **auto_arima_defaults,
        )

        print("\nAuto ARIMA finished.")
        # Optionally print summary if trace is enabled at a high level
        if auto_arima_defaults.get("trace", 0) > 0:
            print(f"Best model summary:\n{model.summary()}")
        else:
            print(
                f"Best model order: {model.order}, seasonal order: {model.seasonal_order}"
            )

        return model

    except Exception as e:
        print(f"Error during auto_arima fitting: {e}")
        import traceback

        traceback.print_exc()
        raise


def predict_sarimax(
    model: pm.arima.ARIMA, h: int, exog_future: Optional[pd.DataFrame] = None
) -> pd.Series:
    """
    Generates forecasts using a fitted pmdarima SARIMAX model.

    Args:
        model (pmdarima.arima.ARIMA): The fitted model object from auto_arima.
        h (int): The forecast horizon (number of steps to predict).
        exog_future (Optional[pd.DataFrame]): Future values of exogenous variables.
                                              Must have h rows and match the columns
                                              used during training. Required if the
                                              model was trained with exogenous variables.

    Returns:
        pd.Series: A Series containing the forecasts, indexed appropriately.
    """
    print(f"Generating SARIMAX forecast for {h} steps...")
    if model.arima_res_.specification.k_exog > 0:  # Check if model used exogenous vars
        if exog_future is None:
            raise ValueError(
                "Model was trained with exogenous variables, but exog_future was not provided."
            )
        if not isinstance(exog_future, pd.DataFrame):
            raise TypeError("exog_future must be a pandas DataFrame.")
        if len(exog_future) != h:
            raise ValueError(
                f"Length of exog_future ({len(exog_future)}) must match the forecast horizon h ({h})."
            )
        # Ensure columns match training (pmdarima uses 'X' internally)
        # Note: pmdarima predict handles column matching internally if names are consistent.

    try:
        # Use model.predict which handles exogenous variables correctly
        # pmdarima automatically generates the future index based on the training data frequency
        forecasts, conf_int = model.predict(
            n_periods=h,
            X=exog_future,  # pmdarima uses 'X' for exogenous
            return_conf_int=True,  # Optional: get confidence intervals
        )
        print("Forecast generation complete.")
        # forecasts is already a pandas Series with appropriate future index
        return forecasts

    except Exception as e:
        print(f"Error during SARIMAX prediction: {e}")
        import traceback

        traceback.print_exc()
        raise
