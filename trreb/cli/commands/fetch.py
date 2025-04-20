"""
Fetch command for TRREB data extractor CLI.
This command handles downloading reports, extracting pages, or both.
"""

import argparse
from pathlib import Path

from trreb.services.fetcher import (
    download_reports,
    extract_page_from_pdf,
    extract_all_pdfs,
    fetch_and_extract_all,
)
from trreb.utils.logging import logger


def fetch(args: argparse.Namespace) -> int:
    """
    CLI command to download and/or extract TRREB PDF data.

    Args:
        args: Parsed arguments from __main__.py

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Logger is already set up in __main__.py
    logger.info(f"Starting fetch command with args: {args}")

    # Determine which operations to perform based on args
    do_download = args.operation in ["fetch", "both"]
    do_extract = args.operation in ["extract", "both"]

    # Setup parameters
    overwrite = getattr(args, "overwrite", False)
    logger.info(
        f"Overwrite mode: {'enabled' if overwrite else 'disabled (skipping existing files)'}"
    )

    # Handle specific PDF extraction
    if do_extract and args.pdf:
        logger.info(f"Processing specific PDF: {args.pdf}")
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            logger.error(f"PDF file {pdf_path} not found.")
            return 1

        # Extract the specific PDF
        result = extract_page_from_pdf(pdf_path, overwrite)

        # Log result
        if result["all_home_types_extracted"]:
            logger.info("✓ ALL HOME TYPES page extracted.")
        else:
            logger.error("✗ Failed to extract ALL HOME TYPES page.")

        if result["detached_extracted"]:
            logger.info("✓ DETACHED page extracted.")
        else:
            logger.error("✗ Failed to extract DETACHED page.")

        return 0

    # Handle both operations together
    if do_download and do_extract:
        logger.info("Performing download and extraction in one operation")

        if args.start_year:
            logger.info(f"Fetching reports starting from year {args.start_year}")
            summary_df = fetch_and_extract_all(args.start_year, overwrite)
        else:
            logger.info("Fetching reports using default start year.")
            summary_df = fetch_and_extract_all(overwrite=overwrite)

        # Log statistics are already handled in the underlying components
        logger.info("Fetch and extract complete!")
        return 0

    # Handle download-only operation
    if do_download:
        logger.info("Performing download-only operation")

        if args.start_year:
            logger.info(f"Downloading reports starting from year {args.start_year}")
            downloaded_files = download_reports(args.start_year)
        else:
            logger.info("Downloading reports using default start year.")
            downloaded_files = download_reports()

        # Log summary
        logger.info(f"Download complete! Downloaded {len(downloaded_files)} files.")
        return 0

    # Handle extract-only operation for all PDFs
    if do_extract:
        logger.info("Performing extract-only operation for all PDFs")
        summary_df = extract_all_pdfs(overwrite)

        # Log statistics are already handled in the underlying components
        logger.info("Extraction complete!")
        return 0

    # Should never reach here
    logger.error("No valid operation specified")
    return 1
