"""
Main entry point for TRREB data extractor CLI.
"""

from trreb.utils.logging import setup_logger
from trreb.cli import cli

# Setup logging
setup_logger()

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()