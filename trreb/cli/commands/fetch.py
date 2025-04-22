"""
Fetch command for TRREB data extractor CLI.
This command handles downloading reports, extracting pages, or both.
"""

import click
from pathlib import Path

from trreb.services.fetcher import (
    download_reports,
    extract_page_from_pdf,
    extract_all_pdfs,
    fetch_and_extract_all,
)
from trreb.utils.logging import logger


@click.command()
@click.option(
    "--operation",
    type=click.Choice(["fetch", "extract", "both"]),
    default="both",
    help="Operation to perform: download reports, extract pages, or both.",
)
@click.option(
    "--start-year",
    type=int,
    help="Start year for fetching reports (defaults to config.START_YEAR).",
)
@click.option(
    "--pdf",
    type=click.Path(exists=True, path_type=Path),
    help="Specific PDF file to extract (only for extract operation).",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing files.",
)
def fetch(operation: str, start_year: int, pdf: Path, overwrite: bool) -> None:
    """Download and/or extract TRREB PDF data."""
    logger.info(f"Starting fetch command with operation: {operation}")

    # Determine which operations to perform
    do_download = operation in ["fetch", "both"]
    do_extract = operation in ["extract", "both"]

    logger.info(
        f"Overwrite mode: {'enabled' if overwrite else 'disabled (skipping existing files)'}"
    )

    # Handle specific PDF extraction
    if do_extract and pdf:
        logger.info(f"Processing specific PDF: {pdf}")
        
        # Extract the specific PDF
        result = extract_page_from_pdf(pdf, overwrite)

        # Log result
        if result["all_home_types_extracted"]:
            logger.info("✓ ALL HOME TYPES page extracted.")
        else:
            logger.error("✗ Failed to extract ALL HOME TYPES page.")

        if result["detached_extracted"]:
            logger.info("✓ DETACHED page extracted.")
        else:
            logger.error("✗ Failed to extract DETACHED page.")

        return

    # Handle both operations together
    if do_download and do_extract:
        logger.info("Performing download and extraction in one operation")

        if start_year:
            logger.info(f"Fetching reports starting from year {start_year}")
            summary_df = fetch_and_extract_all(start_year, overwrite)
        else:
            logger.info("Fetching reports using default start year.")
            summary_df = fetch_and_extract_all(overwrite=overwrite)

        logger.info("Fetch and extract complete!")
        return

    # Handle download-only operation
    if do_download:
        logger.info("Performing download-only operation")

        if start_year:
            logger.info(f"Downloading reports starting from year {start_year}")
            downloaded_files = download_reports(start_year)
        else:
            logger.info("Downloading reports using default start year.")
            downloaded_files = download_reports()

        logger.info(f"Download complete! Downloaded {len(downloaded_files)} files.")
        return

    # Handle extract-only operation for all PDFs
    if do_extract:
        logger.info("Performing extract-only operation for all PDFs")
        summary_df = extract_all_pdfs(overwrite)
        logger.info("Extraction complete!")
        return
