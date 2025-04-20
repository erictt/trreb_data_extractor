"""
Economy command for TRREB data extractor CLI.
"""

import argparse

from trreb.config import PROCESSED_DIR
from trreb.services.economic.integration import (
    integrate_economic_data,
    integrate_economic_data_all,
    prepare_economic_data,
)
from trreb.utils.logging import logger


def economy(args: argparse.Namespace):
    """
    CLI command to download, process, and optionally integrate economic indicators data.
    Accepts parsed arguments from __main__.py.
    """
    # Logger is already set up in __main__.py
    logger.info(f"Starting economy command with args: {args}")

    try:
        # Check if normalized TRREB data exists for integration
        trreb_data_exists = False
        if args.property_type:
            trreb_paths = [PROCESSED_DIR / f"normalized_{args.property_type}.csv"]
            trreb_data_exists = any(path.exists() for path in trreb_paths)
            if not trreb_data_exists:
                logger.warning(
                    f"Normalized TRREB data not found for {args.property_type} at {trreb_paths[0]}. Cannot perform integration."
                )
        else:
            # If no specific type, check if *any* normalized data exists for potential integration later
            trreb_paths = [
                PROCESSED_DIR / "normalized_all_home_types.csv",
                PROCESSED_DIR / "normalized_detached.csv",
            ]
            trreb_data_exists = any(path.exists() for path in trreb_paths)
            if not trreb_data_exists:
                logger.info(
                    "No normalized TRREB data found. Only downloading/preparing economic data."
                )

        # Always prepare economic data (download if needed or forced)
        logger.info("Preparing economic data...")
        econ_df = prepare_economic_data(force_download=args.force_download)
        if econ_df is not None and not econ_df.empty:
            logger.info(
                f"Economic data downloaded/prepared with {len(econ_df)} rows and {len(econ_df.columns)} columns"
            )
        else:
            logger.error("Failed to prepare economic data.")
            return 1  # Indicate failure

        # Proceed with integration only if TRREB data exists and integration is implied (property_type specified)
        if trreb_data_exists and args.property_type:
            logger.info(
                f"Integrating {args.property_type} dataset with economic indicators..."
            )
            df = integrate_economic_data(
                args.property_type,
                include_lags=args.include_lags,
                force_download=args.force_download,  # Pass force_download in case econ data wasn't prepared yet
            )
            if df is not None and not df.empty:
                logger.success(
                    f"Successfully integrated {args.property_type} dataset. Result has {len(df)} rows and {len(df.columns)} columns."
                )
            else:
                logger.error(f"Integration failed for {args.property_type}.")
                # Continue even if integration fails, as economic data might still be useful
        elif trreb_data_exists and not args.property_type:
            # Integrate all datasets if no specific type is given but data exists
            logger.info(
                "Integrating all available datasets with economic indicators..."
            )
            integrated_data = integrate_economic_data_all(
                include_lags=args.include_lags, force_download=args.force_download
            )
            for prop_type, df in integrated_data.items():
                if df is not None and not df.empty:
                    logger.success(
                        f"Successfully integrated {prop_type} dataset. Result has {len(df)} rows and {len(df.columns)} columns."
                    )
                else:
                    logger.warning(
                        f"Integration failed or produced empty result for {prop_type}."
                    )
        elif not trreb_data_exists and args.property_type:
            logger.warning(
                f"Skipping integration for {args.property_type} as normalized TRREB data was not found."
            )

        logger.success("Economic data processing complete!")
        return 0
    except Exception as e:
        logger.exception(f"Error during economic data processing/integration: {e}")
        return 1
