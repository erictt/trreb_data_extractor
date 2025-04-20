#!/usr/bin/env python3
"""
Command-line entry point for the TRREB data extractor.
This module makes the package directly executable with:
    python -m trreb.cli [command] [arguments]
"""

import sys
import argparse
from pathlib import Path

# Add the parent directory to the Python path to support direct execution
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def print_command_help(command):
    """Display help for a specific command."""
    if command == "download":
        print("Download TRREB market reports.")
        print("\nOptions:")
        print("  --start-year YEAR  First year to download (default: 2016)")
        print("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "extract":
        print("Extract specific pages from TRREB PDFs.")
        print("\nOptions:")
        print("  --pdf PDF          Process a specific PDF file (default: process all PDFs)")
        print("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "process":
        print("Process extracted pages into CSV format.")
        print("\nOptions:")
        print("  --type TYPE        Type of property data to process: all_home_types or detached (required)")
        print("  --date DATE        Process a specific date (e.g., 2020-01)")
        print("  --validate         Validate data after processing")
        print("  --normalize        Normalize data after processing")
        print("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "pipeline":
        print("Run the complete TRREB data pipeline.")
        print("\nOptions:")
        print("  --skip-download    Skip downloading PDFs")
        print("  --skip-extract     Skip extracting pages")
        print("  --skip-process     Skip processing CSVs")
        print("  --skip-economic    Skip economic data integration")
        print("  --validate         Validate data after processing")
        print("  --normalize        Normalize data after processing")
        print("  --log-level LEVEL  Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    elif command == "enrich":
        print("Enrich processed data with economic indicators.")
        print("\nOptions:")
        print("  --property-type TYPE  Type of property to enrich: all_home_types or detached (default: both)")
        print("  --include-lags        Include lagged economic indicators (default: true)")
        print("  --log-level LEVEL     Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    
    else:
        print(f"Unknown command: {command}")
        print_main_help()


def print_main_help():
    """Display the main help message."""
    print("TRREB Data Extractor CLI")
    print("\nUsage: python -m trreb.cli COMMAND [OPTIONS]")
    print("\nCommands:")
    print("  download    Download TRREB market reports")
    print("  extract     Extract specific pages from TRREB PDFs")
    print("  process     Process extracted pages into CSV format")
    print("  pipeline    Run the complete data pipeline")
    print("  enrich      Enrich processed data with economic indicators")
    print("\nUse 'python -m trreb.cli COMMAND --help' for help on a specific command.")


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
        # Custom implementation for enrich command
        try:
            # Import functionality
            from trreb.economic.integration import enrich_all_datasets
            
            print("Enriching all datasets with economic indicators...")
            enriched_data = enrich_all_datasets()
            
            # Print statistics for enriched datasets
            for property_type, df in enriched_data.items():
                print(f"Enriched {property_type} dataset with {len(df)} rows and {len(df.columns)} columns")
            
            print("Enrichment complete!")
            return 0
        except Exception as e:
            print(f"Error during enrichment: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    else:
        print(f"Unknown command: {command}")
        print_main_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
