import os
import requests
from datetime import datetime
import concurrent.futures

# Define the base URL and date range
base_url = "https://trreb.ca/wp-content/files/market-stats/market-watch/mw{}{:02d}.pdf"
target_dir = "/Users/eric/workspace/mcp/trreb_data_extractor/pdfs/"

# Create the target directory if it doesn't exist
os.makedirs(target_dir, exist_ok=True)

# Function to download a single file
def download_file(year, month):
    # Format year as 2 digits (e.g., 2016 -> 16)
    year_short = year % 100
    
    # Create the URL
    url = base_url.format(year_short, month)
    
    # Create the output file path
    output_path = os.path.join(target_dir, f"mw{year_short:02d}{month:02d}.pdf")
    
    # Don't re-download if file already exists
    if os.path.exists(output_path):
        print(f"File already exists: {output_path}")
        return True
    
    try:
        # Make the request
        response = requests.get(url, stream=True)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Write the file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded: {url} -> {output_path}")
            return True
        else:
            print(f"Failed to download {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

# Current date to avoid trying to download future dates
current_date = datetime.now()

# Use a thread pool to download files concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    
    # Create download tasks for all months from 2016 to current date
    for year in range(2016, 2026):
        # Determine how many months to process in this year
        max_month = 12
        if year == current_date.year:
            # For current year, only process months up to current month
            max_month = current_date.month
            
        for month in range(1, max_month + 1):
            futures.append(executor.submit(download_file, year, month))
    
    # Wait for all downloads to complete
    downloaded_count = sum(1 for future in concurrent.futures.as_completed(futures) if future.result())

print(f"Download complete. Successfully downloaded {downloaded_count} files.")