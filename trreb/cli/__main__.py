#!/usr/bin/env python3
"""
Command-line entry point for the TRREB data extractor using argparse subcommands.
"""

import sys
import argparse
from pathlib import Path

from trreb.cli.commands import fetch, economy, convert, normalize
from trreb.utils.logging import setup_logger, logger

# Add the parent directory to the Python path to support direct execution
# and importing from trreb package
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def main():
    """
    Main entry point for the command-line interface.
    Uses argparse subparsers to handle different commands.
    """
    parser = argparse.ArgumentParser(
        description="TRREB Data Extractor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global arguments (optional, e.g., log level if consistent across all)
    # parser.add_argument('--log-level', ...)

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- Fetch Command ---
    parser_fetch = subparsers.add_parser(
        "fetch", help="Download and/or extract TRREB market reports."
    )

    parser_fetch.add_argument(
        "operation",
        choices=["fetch", "extract", "both"],
        help="Operation to perform: fetch (download only), extract (extract only), or both",
    )

    parser_fetch.add_argument(
        "--start-year",
        type=int,
        help="First year to download (default: config.START_YEAR), used with fetch and both operations",
    )

    parser_fetch.add_argument(
        "--pdf",
        help="Process a specific PDF file for extraction (default: process all PDFs), used with extract operation",
    )

    parser_fetch.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )

    parser_fetch.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level",
    )

    parser_fetch.set_defaults(func=fetch)

    # --- Convert Command ---
    parser_convert = subparsers.add_parser(
        "convert", help="Convert extracted PDF pages into CSV format."
    )
    parser_convert.add_argument(
        "--type",
        choices=["all_home_types", "detached"],
        required=True,
        help="Type of property data to convert",
    )
    parser_convert.add_argument(
        "--date", help="Convert a specific date (e.g., 2020-01)"
    )
    parser_convert.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing CSV files"
    )
    parser_convert.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level",
    )
    parser_convert.set_defaults(func=convert)
    
    # --- Normalize Command ---
    parser_normalize = subparsers.add_parser(
        "normalize", help="Normalize and optionally validate converted CSV data."
    )
    parser_normalize.add_argument(
        "--type",
        choices=["all_home_types", "detached"],
        required=True,
        help="Type of property data to normalize",
    )
    parser_normalize.add_argument(
        "--date", help="Normalize a specific date (e.g., 2020-01)"
    )
    parser_normalize.add_argument(
        "--validate", action="store_true", help="Validate data before normalization"
    )
    parser_normalize.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level",
    )
    parser_normalize.set_defaults(func=normalize)

    # --- Economy Command ---
    parser_economy = subparsers.add_parser(
        "economy",
        help="Download, process, and optionally integrate economic indicators data.",
    )
    parser_economy.add_argument(
        "--property-type",
        choices=["all_home_types", "detached"],
        help="Type of property to integrate with (optional, needed for integration)",
    )
    parser_economy.add_argument(
        "--include-lags",
        action=argparse.BooleanOptionalAction,  # Use BooleanOptionalAction for --include-lags/--no-include-lags
        default=True,
        help="Include lagged economic indicators during integration",
    )
    parser_economy.add_argument(
        "--force-download",
        action="store_true",
        help="Force download of economic data even if cached data exists",
    )
    parser_economy.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level",
    )
    parser_economy.set_defaults(func=economy)  # Link to function in commands module

    # Parse arguments
    args = parser.parse_args()

    # Setup logger based on parsed arguments (if log_level is present)
    if hasattr(args, "log_level"):
        setup_logger("trreb", level=args.log_level)
    else:
        # Default logger setup if no log_level argument for a command
        setup_logger("trreb", level="INFO")

    # Execute the function associated with the chosen subcommand
    try:
        return args.func(args)  # Pass parsed args to the command function
    except Exception as e:
        logger.exception(f"An error occurred during command execution: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
