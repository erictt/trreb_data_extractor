"""
Economy command for TRREB data extractor CLI.
"""

import click
from pathlib import Path

from trreb.config import PROCESSED_DIR
from trreb.services.economic.integration import (
    integrate_economic_data,
    integrate_economic_data_all,
    prepare_economic_data,
)
from trreb.utils.logging import logger


@click.command()
@click.option(
    "--property-type",
    type=click.Choice(["all_home_types", "detached"]),
    help="Type of property data to integrate with economic indicators.",
)
@click.option(
    "--include-lags",
    is_flag=True,
    default=False,
    help="Include lagged economic indicators in the integration.",
)
@click.option(
    "--force-download",
    is_flag=True,
    default=False,
    help="Force download of economic data even if it exists locally.",
)
def economy(property_type: str, include_lags: bool, force_download: bool) -> None:
    """Download, process, and optionally integrate economic indicators data."""
    logger.info("Starting economy command")

    try:
        # Check if normalized TRREB data exists for integration
        trreb_data_exists = False
        if property_type:
            trreb_paths = [Path(PROCESSED_DIR) / f"normalized_{property_type}.csv"]
            trreb_data_exists = any(path.exists() for path in trreb_paths)
            if not trreb_data_exists:
                logger.warning(
                    f"Normalized TRREB data not found for {property_type} at {trreb_paths[0]}. Cannot perform integration."
                )
        else:
            # If no specific type, check if *any* normalized data exists for potential integration later
            trreb_paths = [
                Path(PROCESSED_DIR) / "normalized_all_home_types.csv",
                Path(PROCESSED_DIR) / "normalized_detached.csv",
            ]
            trreb_data_exists = any(path.exists() for path in trreb_paths)
            if not trreb_data_exists:
                logger.info(
                    "No normalized TRREB data found. Only downloading/preparing economic data."
                )

        # Always prepare economic data (download if needed or forced)
        logger.info("Preparing economic data...")
        econ_df = prepare_economic_data(force_download=force_download)
        if econ_df is not None and not econ_df.empty:
            logger.info(
                f"Economic data downloaded/prepared with {len(econ_df)} rows and {len(econ_df.columns)} columns"
            )
        else:
            logger.error("Failed to prepare economic data.")
            raise click.Abort()

        # Proceed with integration only if TRREB data exists and integration is implied (property_type specified)
        if trreb_data_exists and property_type:
            logger.info(
                f"Integrating {property_type} dataset with economic indicators..."
            )
            df = integrate_economic_data(
                property_type,
                include_lags=include_lags,
                force_download=force_download,  # Pass force_download in case econ data wasn't prepared yet
            )
            if df is not None and not df.empty:
                logger.success(
                    f"Successfully integrated {property_type} dataset. Result has {len(df)} rows and {len(df.columns)} columns."
                )
            else:
                logger.error(f"Integration failed for {property_type}.")
                # Continue even if integration fails, as economic data might still be useful
        elif trreb_data_exists and not property_type:
            # Integrate all datasets if no specific type is given but data exists
            logger.info(
                "Integrating all available datasets with economic indicators..."
            )
            integrated_data = integrate_economic_data_all(
                include_lags=include_lags, force_download=force_download
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
        elif not trreb_data_exists and property_type:
            logger.warning(
                f"Skipping integration for {property_type} as normalized TRREB data was not found."
            )

        logger.success("Economic data processing complete!")

    except Exception as e:
        logger.exception(f"Error during economic data processing/integration: {e}")
        raise click.Abort()