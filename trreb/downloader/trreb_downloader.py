"""
Module for downloading TRREB market reports.
"""

import concurrent.futures
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
from tqdm import tqdm

from trreb.config import (
    MAX_DOWNLOAD_WORKERS, PDF_DIR, START_YEAR, TRREB_BASE_URL
)
from trreb.utils.logging import logger


class TrrebDownloader:
    """Class for downloading TRREB market reports."""
    
    def __init__(self, target_dir: Path = PDF_DIR):
        """
        Initialize the downloader.
        
        Args:
            target_dir: Directory to save downloaded PDFs
        """
        self.base_url = TRREB_BASE_URL
        self.target_dir = target_dir
        
        # Create the target directory if it doesn't exist
        os.makedirs(self.target_dir, exist_ok=True)
        
        # Current date to avoid trying to download future dates
        self.current_date = datetime.now()
    
    def download_file(self, year: int, month: int) -> bool:
        """
        Download a single TRREB market report file.
        
        Args:
            year: Year of the report (e.g., 2016)
            month: Month of the report (1-12)
            
        Returns:
            True if download was successful, False otherwise
        """
        # Format year as 2 digits (e.g., 2016 -> 16)
        year_short = year % 100

        # Create the URL
        url = self.base_url.format(year_short, month)

        # Create the output file path
        output_path = os.path.join(self.target_dir, f"mw{year_short:02d}{month:02d}.pdf")

        # Don't re-download if file already exists
        if os.path.exists(output_path):
            logger.debug(f"File already exists: {output_path}")
            return True

        try:
            # Make the request
            response = requests.get(url, stream=True)

            # Check if the request was successful
            if response.status_code == 200:
                # Write the file
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Downloaded: {url} -> {output_path}")
                return True
            else:
                logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def download_all(self, start_year: int = START_YEAR) -> List[Path]:
        """
        Download all available TRREB market reports.
        
        Args:
            start_year: First year to download (default: 2016)
            
        Returns:
            List of paths to downloaded files
        """
        logger.info(f"Starting download from year {start_year} to current date {self.current_date.year}-{self.current_date.month}")
        
        # Check if PDF directory exists and is writable
        logger.info(f"Target directory: {self.target_dir} (exists: {self.target_dir.exists()})")
        
        # Use a thread pool to download files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as executor:
            futures = []

            # Create download tasks for all months from start_year to current date
            for year in range(start_year, self.current_date.year + 1):
                # Determine how many months to process in this year
                max_month = 12
                if year == self.current_date.year:
                    # For current year, only process months up to current month
                    max_month = self.current_date.month

                for month in range(1, max_month + 1):
                    logger.debug(f"Adding download task for {year}-{month}")
                    futures.append(executor.submit(self.download_file, year, month))

            # Track progress
            total = len(futures)
            successful = 0
            
            logger.info(f"Created {total} download tasks")
            
            # Wait for all downloads to complete
            for future in tqdm(
                concurrent.futures.as_completed(futures), 
                total=total, 
                desc="Downloading reports"
            ):
                if future.result():
                    successful += 1

        logger.success(f"Download complete. Successfully downloaded {successful}/{total} files.")
        
        # Return list of downloaded files
        downloaded_files = [p for p in self.target_dir.glob('*.pdf') if p.is_file()]
        logger.info(f"Found {len(downloaded_files)} PDF files in target directory")
        
        return downloaded_files


# Convenience function for command-line use
def download_reports(start_year: Optional[int] = None) -> List[Path]:
    """
    Download all available TRREB market reports.
    
    Args:
        start_year: First year to download (default: config.START_YEAR)
        
    Returns:
        List of paths to downloaded files
    """
    logger.debug("Inside download_reports function")
    logger.debug(f"Creating TrrebDownloader with target_dir={PDF_DIR}")
    downloader = TrrebDownloader()
    
    if start_year:
        logger.debug(f"Calling download_all with start_year={start_year}")
        return downloader.download_all(start_year)
    
    from trreb.config import START_YEAR
    logger.debug(f"Calling download_all with default start_year={START_YEAR}")
    return downloader.download_all()
