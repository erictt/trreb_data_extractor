import pandas as pd
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
)
import matplotlib.pyplot as plt
from typing import Dict, Optional


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    """
    Calculates standard regression metrics for forecast evaluation.

    Args:
        y_true (pd.Series): The actual target values.
        y_pred (pd.Series): The predicted values from the model.

    Returns:
        Dict[str, float]: A dictionary containing MAE, RMSE, and MAPE.
                          Returns NaN for MAPE if y_true contains zeros.
    """
    if not isinstance(y_true, pd.Series):
        y_true = pd.Series(y_true)
    if not isinstance(y_pred, pd.Series):
        y_pred = pd.Series(y_pred)

    # Ensure indices match for proper calculation
    y_true_aligned, y_pred_aligned = y_true.align(y_pred, join="inner")

    if y_true_aligned.empty or y_pred_aligned.empty:
        print(
            "Warning: No overlapping data points between y_true and y_pred after alignment."
        )
        return {"MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan}

    metrics = {}
    metrics["MAE"] = mean_absolute_error(y_true_aligned, y_pred_aligned)
    metrics["RMSE"] = np.sqrt(mean_squared_error(y_true_aligned, y_pred_aligned))

    # Handle potential zeros in y_true for MAPE calculation
    # Add a small epsilon to avoid division by zero if strictly needed,
    # but sklearn's implementation handles infinite values.
    # Check for zeros mainly to warn the user about potential interpretation issues.
    if (y_true_aligned == 0).any():
        print(
            "Warning: MAPE calculation might be unstable due to zero values in y_true."
        )
        # Calculate MAPE anyway, sklearn handles inf results if necessary
        metrics["MAPE"] = (
            mean_absolute_percentage_error(y_true_aligned, y_pred_aligned) * 100
        )  # As percentage
        # Replace inf with NaN if desired, though sklearn's output might be preferred
        # metrics['MAPE'] = metrics['MAPE'] if np.isfinite(metrics['MAPE']) else np.nan
    else:
        metrics["MAPE"] = (
            mean_absolute_percentage_error(y_true_aligned, y_pred_aligned) * 100
        )  # As percentage

    print("Calculated Metrics:")
    for name, value in metrics.items():
        print(f"  {name}: {value:.4f}")

    return metrics


def plot_forecast(
    y_true: pd.Series,
    y_pred: pd.Series,
    title: str = "Actual vs. Forecast",
    y_train: Optional[pd.Series] = None,
    output_path: Optional[str] = None,
):
    """
    Generates a plot comparing actual values and forecasted values over time.

    Args:
        y_true (pd.Series): The actual target values (test set).
        y_pred (pd.Series): The predicted values from the model (test set).
        title (str): The title for the plot.
        y_train (Optional[pd.Series]): Training data actuals to include for context.
        output_path (Optional[str]): If provided, saves the plot to this file path.
                                     If None, displays the plot.
    """
    plt.figure(figsize=(12, 6))

    if y_train is not None:
        # Ensure y_train is a Series for consistent plotting
        if not isinstance(y_train, pd.Series):
            y_train = pd.Series(y_train)
        plt.plot(y_train.index, y_train, label="Training Data", color="gray", alpha=0.7)

    # Ensure y_true and y_pred are Series for consistent plotting
    if not isinstance(y_true, pd.Series):
        y_true = pd.Series(y_true)
    if not isinstance(y_pred, pd.Series):
        y_pred = pd.Series(y_pred)

    # Align predictions with true values for plotting
    y_true_aligned, y_pred_aligned = y_true.align(y_pred, join="inner")

    if y_true_aligned.empty or y_pred_aligned.empty:
        print(
            "Warning: No overlapping data points between y_true and y_pred after alignment. Cannot plot."
        )
        plt.close()  # Close the empty figure
        return

    plt.plot(
        y_true_aligned.index,
        y_true_aligned,
        label="Actual (Test)",
        color="blue",
        marker=".",
        linestyle="-",
    )
    plt.plot(
        y_pred_aligned.index,
        y_pred_aligned,
        label="Forecast (Test)",
        color="red",
        linestyle="--",
    )

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(y_true.name or "Value")  # Use Series name if available
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()  # Adjust layout to prevent labels overlapping

    if output_path:
        try:
            plt.savefig(output_path, bbox_inches="tight")  # Use bbox_inches='tight'
            print(f"Plot saved to: {output_path}")
        except Exception as e:
            print(f"Error saving plot to {output_path}: {e}")
        finally:
            plt.close()  # Close the plot figure after saving or error
    else:
        try:
            plt.show()  # Display the plot interactively
        except Exception as e:
            print(f"Error displaying plot: {e}")
        finally:
            plt.close()  # Close the plot figure after displaying or error
