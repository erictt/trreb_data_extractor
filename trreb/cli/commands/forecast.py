import click
import pandas as pd
import numpy as np
import os
import json
import joblib  # For saving models
from datetime import datetime

# Import project configuration for paths
from trreb.config import PROCESSED_DIR, FORECAST_DIR

# Import forecasting service modules
from trreb.services.forecasting.preparation import prepare_forecasting_data
from trreb.services.forecasting.split import split_data_chronological
from trreb.services.forecasting.sarimax_model import train_sarimax, predict_sarimax
from trreb.services.forecasting.lgbm_model import train_lgbm, predict_lgbm
from trreb.services.forecasting.evaluation import calculate_metrics, plot_forecast

from trreb.utils.logging import logger


@click.command()
@click.option(
    "--input-type",
    type=click.Choice(["all_home_types", "detached"], case_sensitive=False),
    default="all_home_types",
    show_default=True,
    help="Type of housing data to use.",
)
@click.option(
    "--model-type",
    type=click.Choice(["sarimax", "lgbm", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Which model(s) to run.",
)
@click.option(
    "--target-variable",
    default="Median Price",
    show_default=True,
    help="The variable to forecast.",
)
@click.option(
    "--forecast-horizon",
    type=int,
    default=6,
    show_default=True,
    help="Number of months ahead to forecast.",
)
@click.option(
    "--region",
    default="TRREB Total",
    show_default=True,
    help="The specific region to forecast.",
)
# Updated help text to reference FORECAST_DIR from config
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default=None,
    help="Directory to save results. Defaults to FORECAST_DIR defined in config.",
)
@click.option(
    "--save-model",
    is_flag=True,
    default=False,
    help="Save the trained model(s) to the output directory.",
)
@click.option(
    "--plot", is_flag=True, default=False, help="Generate and save forecast plots."
)
def forecast(
    input_type,
    model_type,
    target_variable,
    forecast_horizon,
    region,
    output_dir,
    save_model,
    plot,
):
    """
    Runs the time series forecasting pipeline for TRREB housing data.

    Prepares data, splits chronologically, trains the specified model(s)
    (SARIMAX, LightGBM), generates predictions on the test set,
    evaluates performance, and saves results.
    """
    # Setup logging if available
    logger.info("Starting forecast command...")
    # --- 1. Resolve Paths using trreb.config ---
    try:
        # Construct input path using PROCESSED_DIR from config
        input_filename = f"integrated_economic_{input_type}.csv"
        input_path = os.path.join(PROCESSED_DIR, input_filename)

        # Determine base output directory using FORECAST_DIR from config as default
        if output_dir:
            # User provided a specific output directory
            base_output_dir = output_dir
            logger.info(f"Using user-provided base output directory: {base_output_dir}")
        else:
            # Use default: FORECAST_DIR from config
            base_output_dir = FORECAST_DIR
            logger.info(
                f"Using FORECAST_DIR from config as base output directory: {base_output_dir}"
            )

        # Create a timestamped subdirectory for this run's outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = os.path.join(
            base_output_dir,
            f"{input_type}_{target_variable.replace(' ', '')}_{region.replace(' ', '')}_{timestamp}",
        )
        os.makedirs(run_output_dir, exist_ok=True)  # Create base and run-specific dirs

        logger.info(f"Using PROCESSED_DIR from config: {PROCESSED_DIR}")
        logger.info(f"Input data path: {input_path}")
        logger.info(f"Output directory for this run: {run_output_dir}")

    except FileNotFoundError:
        logger.error(f"Input file not found. Constructed path: {input_path}")
        return
    except NameError as e:
        logger.error(f"Configuration error: {e}. Check trreb.config.")
        logger.error(f"Error: Missing directory configuration in trreb.config: {e}")
        return
    except Exception:
        logger.exception("Error resolving paths.")
        return

    # --- 2. Prepare Data ---
    logger.info("\n--- Preparing Data ---")
    prepared_target_col = f"{target_variable}_t_plus_{forecast_horizon}"
    try:
        prepared_df = prepare_forecasting_data(
            input_path=input_path,
            region_filter=region,
            target_variable=target_variable,
            forecast_horizon=forecast_horizon,
            # Add options to customize features/lags if needed
        )
        if prepared_df.empty:
            logger.error(
                "Error: Prepared DataFrame is empty after processing. Check data or parameters."
            )
            return
        logger.info(f"Prepared data shape: {prepared_df.shape}")
        # Save prepared data (optional)
        prepared_data_path = os.path.join(run_output_dir, "prepared_data.csv")
        prepared_df.to_csv(prepared_data_path)
        logger.info(f"Saved prepared data to {prepared_data_path}")

    except Exception:
        logger.exception("Error during data preparation.")
        import traceback

        traceback.print_exc()
        return

    # --- 3. Split Data ---
    logger.info("\n--- Splitting Data ---")
    try:
        # We use the shifted target column for splitting X/y correctly for both models
        X_train, X_val, X_test, y_train_shifted, y_val_shifted, y_test_shifted = (
            split_data_chronological(
                df=prepared_df,
                target_col=prepared_target_col,  # Use the shifted target for splitting X/y
                test_size=0.15,  # Consider making these configurable
                validation_size=0.15,
            )
        )
        logger.info(f"Train shapes: X={X_train.shape}, y={y_train_shifted.shape}")
        logger.info(f"Validation shapes: X={X_val.shape}, y={y_val_shifted.shape}")
        logger.info(f"Test shapes: X={X_test.shape}, y={y_test_shifted.shape}")
    except Exception as e:
        logger.exception("Error during data splitting.")
        return

    results = {}  # To store metrics and prediction file paths

    # --- 4. Run SARIMAX Model (if requested) ---
    if model_type in ["sarimax", "all"]:
        logger.info("\n--- Running SARIMAX Model ---")
        try:
            # Prepare data specifically for SARIMAX
            y_train_sarimax = prepared_df.loc[X_train.index, target_variable]
            exog_train_sarimax = X_train
            exog_test_sarimax = X_test  # Use test features as future exogenous

            # Train
            sarimax_model = train_sarimax(
                y_train=y_train_sarimax,
                exog_train=exog_train_sarimax,
                m=12,  # Assuming monthly data
                trace=0,  # Reduce verbosity in CLI run
            )

            # Predict
            test_horizon = len(exog_test_sarimax)
            sarimax_preds = predict_sarimax(
                model=sarimax_model, h=test_horizon, exog_future=exog_test_sarimax
            )

            # Evaluate (compare against the *original* target in the test period)
            y_test_original = prepared_df.loc[X_test.index, target_variable]
            sarimax_metrics = calculate_metrics(
                y_true=y_test_original, y_pred=sarimax_preds
            )
            results["SARIMAX"] = {"metrics": sarimax_metrics}

            # Save predictions
            sarimax_preds_df = pd.DataFrame(
                {"Actual": y_test_original, "Predicted": sarimax_preds}
            )
            sarimax_preds_path = os.path.join(run_output_dir, "predictions_sarimax.csv")
            sarimax_preds_df.to_csv(sarimax_preds_path)
            results["SARIMAX"]["predictions_path"] = sarimax_preds_path
            logger.info(f"SARIMAX predictions saved to {sarimax_preds_path}")

            # Plot
            if plot:
                plot_path = os.path.join(run_output_dir, "plot_sarimax.png")
                plot_forecast(
                    y_true=y_test_original,
                    y_pred=sarimax_preds,
                    y_train=y_train_sarimax,  # Plot original training target
                    title=f"SARIMAX Forecast vs Actual ({target_variable} - {region})",
                    output_path=plot_path,
                )
                results["SARIMAX"]["plot_path"] = plot_path

            # Save model
            if save_model:
                model_path = os.path.join(run_output_dir, "model_sarimax.joblib")
                joblib.dump(sarimax_model, model_path)
                results["SARIMAX"]["model_path"] = model_path
                logger.info(f"SARIMAX model saved to {model_path}")

        except Exception as e:
            logger.exception("Error during SARIMAX pipeline.")
            results["SARIMAX"] = {"error": str(e)}
            import traceback

            traceback.print_exc()

    # --- 5. Run LightGBM Model (if requested) ---
    if model_type in ["lgbm", "all"]:
        logger.info("\n--- Running LightGBM Model ---")
        try:
            # Train (using shifted target directly)
            lgbm_model = train_lgbm(
                X_train=X_train,
                y_train=y_train_shifted,  # Train on y_{t+h}
                X_val=X_val,
                y_val=y_val_shifted,  # Validate on y_{t+h}
                early_stopping_rounds=50,
                verbose=-1,  # Reduce verbosity in CLI run
            )

            # Predict
            lgbm_preds = predict_lgbm(model=lgbm_model, X_future=X_test)

            # Evaluate (compare against the shifted target in the test set)
            lgbm_metrics = calculate_metrics(y_true=y_test_shifted, y_pred=lgbm_preds)
            results["LightGBM"] = {"metrics": lgbm_metrics}

            # Save predictions
            lgbm_preds_df = pd.DataFrame(
                {"Actual": y_test_shifted, "Predicted": lgbm_preds}
            )
            lgbm_preds_path = os.path.join(run_output_dir, "predictions_lgbm.csv")
            lgbm_preds_df.to_csv(lgbm_preds_path)
            results["LightGBM"]["predictions_path"] = lgbm_preds_path
            logger.info(f"LightGBM predictions saved to {lgbm_preds_path}")

            # Plot
            if plot:
                plot_path = os.path.join(run_output_dir, "plot_lgbm.png")
                plot_forecast(
                    y_true=y_test_shifted,  # Plot shifted target
                    y_pred=lgbm_preds,
                    y_train=y_train_shifted,  # Plot shifted training target
                    title=f"LightGBM Forecast vs Actual ({prepared_target_col} - {region})",
                    output_path=plot_path,
                )
                results["LightGBM"]["plot_path"] = plot_path

            # Save model
            if save_model:
                model_path = os.path.join(run_output_dir, "model_lgbm.joblib")
                joblib.dump(lgbm_model, model_path)
                results["LightGBM"]["model_path"] = model_path
                logger.info(f"LightGBM model saved to {model_path}")

        except Exception as e:
            logger.exception("Error during LightGBM pipeline.")
            results["LightGBM"] = {"error": str(e)}
            import traceback

            traceback.print_exc()

    # --- 6. Save Overall Results ---
    logger.info("\n--- Saving Run Summary ---")
    summary_path = os.path.join(run_output_dir, "run_summary.json")
    run_config = {
        "input_type": input_type,
        "model_type_run": model_type,
        "target_variable": target_variable,
        "forecast_horizon": forecast_horizon,
        "region": region,
        "timestamp": timestamp,
        "input_path": input_path,
        "output_directory": run_output_dir,
    }
    # Convert numpy types to standard Python types for JSON serialization
    serializable_results = json.loads(
        json.dumps(
            results,
            default=lambda x: str(x)
            if isinstance(
                x,
                (
                    np.int_,
                    np.intc,
                    np.intp,
                    np.int8,
                    np.int16,
                    np.int32,
                    np.int64,
                    np.uint8,
                    np.uint16,
                    np.uint32,
                    np.uint64,
                    np.float_,
                    np.float16,
                    np.float32,
                    np.float64,
                ),
            )
            else x,
        )
    )

    summary_data = {"config": run_config, "results": serializable_results}
    try:
        with open(summary_path, "w") as f:
            json.dump(summary_data, f, indent=4)
        logger.info(f"Run summary saved to {summary_path}")
    except Exception:
        logger.exception("Failed to save run summary.")

    logger.info("\n--- Forecast Pipeline Complete ---")
