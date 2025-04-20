#!/usr/bin/env python3
"""
Command-line entry point for the TRREB data extractor.
This module makes the package directly executable with:
    python -m trreb.cli [command] [arguments]
"""

import sys
import argparse
from pathlib import Path

from trreb.utils.logging import logger

# Add the parent directory to the Python path to support direct execution
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def print_command_help(command):
    """Display help for a specific command."""
    if command == "download":
        logger.info("Download TRREB market reports.")
        logger.info("\nOptions:")
        logger.info("  --start-year YEAR  First year to download (default: 2016)")
        logger.info("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "extract":
        logger.info("Extract specific pages from TRREB PDFs.")
        logger.info("\nOptions:")
        logger.info("  --pdf PDF          Process a specific PDF file (default: process all PDFs)")
        logger.info("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "process":
        logger.info("Process extracted pages into CSV format.")
        logger.info("\nOptions:")
        logger.info("  --type TYPE        Type of property data to process: all_home_types or detached (required)")
        logger.info("  --date DATE        Process a specific date (e.g., 2020-01)")
        logger.info("  --validate         Validate data after processing")
        logger.info("  --normalize        Normalize data after processing")
        logger.info("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "pipeline":
        logger.info("Run the complete TRREB data pipeline.")
        logger.info("\nOptions:")
        logger.info("  --skip-download    Skip downloading PDFs")
        logger.info("  --skip-extract     Skip extracting pages")
        logger.info("  --skip-process     Skip processing CSVs")
        logger.info("  --skip-economic    Skip economic data integration")
        logger.info("  --validate         Validate data after processing")
        logger.info("  --normalize        Normalize data after processing")
        logger.info("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "economy":
        logger.info("Download and process economic indicators data.")
        logger.info("\nOptions:")
        logger.info("  --property-type TYPE  Type of property to integrate with: all_home_types or detached (default: both)")
        logger.info("  --include-lags        Include lagged economic indicators (default: true)")
        logger.info("  --force-download      Force re-download of economic data even if cached data exists")
        logger.info("  --log-level LEVEL     Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    else:
        logger.warning(f"Unknown command: {command}")
        print_main_help()


def print_main_help():
    """Display the main help message."""
    logger.info("TRREB Data Extractor CLI")
    logger.info("\nUsage: python -m trreb.cli COMMAND [OPTIONS]")
    logger.info("\nCommands:")
    logger.info("  download    Download TRREB market reports")
    logger.info("  extract     Extract specific pages from TRREB PDFs")
    logger.info("  process     Process extracted pages into CSV format")
    logger.info("  pipeline    Run the complete data pipeline")
    logger.info("  economy     Download and process economic indicators data")
    logger.info("\nUse 'python -m trreb.cli COMMAND --help' for help on a specific command.")


def main():
    """
    Main entry point for the command-line interface.
    Parses the command and delegates to the appropriate function.
    """
    # Need at least one argument (the command)
    if len(sys.argv) < 2:
        print_main_help()
        return 1
    
    # Get the command
    command = sys.argv[1].lower()
    
    # Handle help requests
    if command in ["-h", "--help"]:
        print_main_help()
        return 0
    
    # Handle command-specific help
    if len(sys.argv) > 2 and sys.argv[2] in ["-h", "--help"]:
        print_command_help(command)
        return 0
    
    # Delegate to the appropriate command function
    if command == "download":
        # Import here to avoid circular dependencies
        from trreb.cli.commands import download
        # Remove the command from sys.argv
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return download()
    
    elif command == "extract":
        from trreb.cli.commands import extract_pages
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return extract_pages()
    
    elif command == "process":
        from trreb.cli.commands import process
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return process()
    
    elif command == "pipeline":
        # Import here to avoid circular imports
        from scripts.run_pipeline import main as run_pipeline
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return run_pipeline()
    
    elif command == "enrich":
        # Redirect to economy command with a deprecation warning
        logger.warning("The 'enrich' command is deprecated. Please use 'economy' instead.")
        command = "economy"
        # Fall through to the economy command
    
    elif command == "economy":
        # Parse arguments for economy command
        parser = argparse.ArgumentParser(description="Download and process economic indicators data.")
        parser.add_argument("--property-type", choices=["all_home_types", "detached"], 
                           help="Type of property to enrich (default: both)")
        parser.add_argument("--include-lags", action="store_true", default=True,
                           help="Include lagged economic indicators (default: true)")
        parser.add_argument("--force-download", action="store_true", 
                           help="Force download of economic data even if cached data exists")
        parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                           default="INFO", help="Set the logging level")
        
        # Parse the arguments
        args = parser.parse_args(sys.argv[2:])
        
        # Setup logger
        from trreb.utils.logging import setup_logger, logger
        setup_logger("trreb", level=args.log_level)
        
        try:
            # Import functionality
            from trreb.economic.integration import enrich_trreb_data, enrich_all_datasets, prepare_economic_data
            from trreb.config import PROCESSED_DIR
            
            # Check if normalized TRREB data exists
            if args.property_type:
                trreb_paths = [PROCESSED_DIR / f"normalized_{args.property_type}.csv"]
            else:
                trreb_paths = [
                    PROCESSED_DIR / "normalized_all_home_types.csv",
                    PROCESSED_DIR / "normalized_detached.csv"
                ]
            
            trreb_data_exists = any(path.exists() for path in trreb_paths)
            
            if not trreb_data_exists:
                # If no TRREB data exists, just download and prepare economic data
                logger.info("No normalized TRREB data found. Downloading economic data only...")
                econ_df = prepare_economic_data(force_download=args.force_download)
                logger.info(f"Economic data downloaded and prepared with {len(econ_df)} rows and {len(econ_df.columns)} columns")
            else:
                # TRREB data exists, proceed with enrichment
                if args.property_type:
                    # Enrich specific property type
                    logger.info(f"Enriching {args.property_type} dataset with economic indicators...")
                    df = enrich_trreb_data(args.property_type, include_lags=args.include_lags, 
                                         force_download=args.force_download)
                    if not df.empty:
                        logger.info(f"Enriched {args.property_type} dataset with {len(df)} rows and {len(df.columns)} columns")
                else:
                    # Enrich all datasets
                    logger.info("Enriching all datasets with economic indicators...")
                    enriched_data = enrich_all_datasets(include_lags=args.include_lags, 
                                                      force_download=args.force_download)
                    
                    # Print statistics for enriched datasets
                    for property_type, df in enriched_data.items():
                        if not df.empty:
                            logger.info(f"Enriched {property_type} dataset with {len(df)} rows and {len(df.columns)} columns")
            
            logger.info("Economic data processing complete!")
            return 0
        except Exception as e:
            logger.error(f"Error during enrichment: {e}")
            return 1
    
    else:
        logger.warning(f"Unknown command: {command}")
        print_main_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
