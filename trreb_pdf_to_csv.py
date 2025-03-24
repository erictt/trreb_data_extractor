#!/usr/bin/env python3
"""
TRREB PDF to CSV Converter

This script converts Toronto Regional Real Estate Board (TRREB) Market Watch PDFs to CSV format
using the Google Gemini API. It supports filtering by year and property type.

Usage:
    python trreb_pdf_to_csv.py --year 2024 --property_type "ALL_HOME" --api_key "your_api_key"
    python trreb_pdf_to_csv.py --year all --property_type "ALL_HOME" --api_key "your_api_key"
"""

import os
import argparse
import glob
import re
import csv
import google.generativeai as genai
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("trreb_pdf_to_csv.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Constants
PDF_DIR = "/Users/eric/workspace/mcp/trreb_data_extractor/split-pdfs"
OUTPUT_DIR = "/Users/eric/workspace/mcp/trreb_data_extractor/csv-outputs"
PROPERTY_TYPES = [
    "ALL_HOME",
    "CONDO_APT",
    "CONDO_TOWNHOUSE",
    "DETACHED",
    "SEMI-DETACHED",
    "TOWNHOUSE",
]
AVAILABLE_YEARS = [str(year) for year in range(2016, 2026)]  # 2016 to 2025


def setup_gemini_api(api_key):
    """Initialize the Gemini API client with the provided API key."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def read_pdf_content(pdf_path):
    """Read the content of a PDF file."""
    try:
        with open(pdf_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return None


def extract_data_with_gemini(model, pdf_content, pdf_path):
    """Use Gemini API to extract structured data from the PDF content."""
    if not pdf_content:
        return None

    # Get file name for context
    filename = os.path.basename(pdf_path)

    # Create prompt for Gemini model
    prompt = f"""
    Extract real estate market data from this TRREB (Toronto Regional Real Estate Board) Market Watch PDF.
    
    The PDF is named: {filename}
    
    Extract all tabular data including:
    1. Region/Municipality names (may be labeled as Region, Sub_Municipality, or # of Sales)
    2. Number of sales (may be labeled as "# of Sales" or "Number of Sales")
    3. Dollar Volume
    4. Average Price
    5. Median Price
    6. New Listings
    7. SNLR (Trend) if available
    8. Active Listings
    9. Mos. Inv. (Trend) if available
    10. Avg. SP/LP ratio
    11. Avg. DOM (Days on Market)
    12. Avg. LDOM (Listing Days on Market) if available
    13. Avg. PDOM (Property Days on Market) if available
    
    Format the output as a plain CSV file with headers for each column.
    
    IMPORTANT: 
    - DO NOT include any Markdown formatting (no ```csv or ``` markers).
    - DO NOT include any explanations or surrounding text.
    - Start directly with the CSV header row.
    - End with the last data row.
    - Include a header row with column names.
    - Use simple, clean column names WITHOUT any superscript notations or symbols.
      For example, use "Median Price" instead of "Median Price¹" or "Median Price^1"
    - Remove any footnote numbers or symbols from the column headers.
    - Use consistent column names for all data.
    - If a data point in a cell is missing, leave it blank in the CSV.
    - Make sure to include all regions/municipalities listed in the table.
    
    Your output should look exactly like a proper CSV file that starts with the header row.
    """

    try:
        # Generate content with Gemini API
        response = model.generate_content(
            [prompt, {"mime_type": "application/pdf", "data": pdf_content}]
        )
        
        # Get the response text and clean it
        result_text = response.text
        
        # Log a preview of the response
        preview = result_text[:100] + "..." if len(result_text) > 100 else result_text
        logger.info(f"Received response from Gemini API (preview): {preview}")
        
        return result_text
    except Exception as e:
        logger.error(f"Error with Gemini API for {pdf_path}: {e}")
        return None


def clean_column_headers(csv_content):
    """Clean column headers by removing superscript notations and standardizing names."""
    if not csv_content:
        return csv_content
    
    lines = csv_content.split('\n')
    if not lines:
        return csv_content
    
    # Process the header line
    header = lines[0]
    
    # Map of raw header patterns to standardized names
    header_patterns = {
        r'(?:Region/Municipality|Region|Sub_Municipality|# of Sales)': 'Region/Municipality',
        r'(?:Number of Sales|# of Sales)': 'Number of Sales',
        r'Dollar Volume\s*\d*': 'Dollar Volume',
        r'Average Price\s*\d*': 'Average Price',
        r'Median Price\s*\d*': 'Median Price',
        r'New Listings\s*\d*': 'New Listings',
        r'SNLR\s*\(Trend\)\s*\d*': 'SNLR (Trend)',
        r'Active Listings\s*\d*': 'Active Listings',
        r'Mos\.\s*Inv\.\s*\(Trend\)\s*\d*': 'Mos. Inv. (Trend)',
        r'Avg\.\s*SP\s*[/]?\s*LP\s*\d*': 'Avg. SP/LP',
        r'Avg\.\s*DOM\s*\d*': 'Avg. DOM',
        r'Avg\.\s*LDOM\s*\d*': 'Avg. LDOM',
        r'Avg\.\s*PDOM\s*\d*': 'Avg. PDOM'
    }
    
    # Create column map with indexes
    column_map = {}
    header_cols = header.split(',')
    
    # Clean each column individually
    cleaned_cols = []
    for i, col in enumerate(header_cols):
        col = col.strip()
        cleaned = col
        
        # Remove any numeric superscripts or special characters
        for pattern, replacement in header_patterns.items():
            if re.match(pattern, col, re.IGNORECASE):
                cleaned = replacement
                break
        
        # Add to cleaned columns
        cleaned_cols.append(cleaned)
    
    # Replace the header with cleaned version
    lines[0] = ','.join(cleaned_cols)
    
    # Reconstruct the CSV content
    return '\n'.join(lines)

def save_to_csv(csv_content, output_path):
    """Save the extracted CSV content to a file."""
    if not csv_content:
        return False

    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Clean CSV content to remove Markdown code block markers
        cleaned_content = csv_content
        
        # Remove any Markdown code block markers (```csv, ```, etc.)
        if cleaned_content.startswith("```"):
            # Find the end of the first line
            first_newline = cleaned_content.find("\n")
            if first_newline > 0:
                cleaned_content = cleaned_content[first_newline + 1:]
        
        # Also remove trailing code block markers if present
        if cleaned_content.strip().endswith("```"):
            cleaned_content = cleaned_content.strip()[:-3].strip()
        
        # Clean column headers by removing superscript notations
        cleaned_content = clean_column_headers(cleaned_content)
        
        # Write cleaned CSV content to file
        with open(output_path, "w", newline="") as f:
            f.write(cleaned_content)
            
        logger.info(f"Cleaned CSV content and saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving CSV {output_path}: {e}")
        return False


def process_pdf(model, pdf_path, output_dir):
    """Process a single PDF file and convert to CSV."""
    # Extract year, month, and property type from filename
    filename = os.path.basename(pdf_path)
    match = re.match(r"([A-Z_]+)_(\d{4})_(\d{2})\.pdf", filename)

    if not match:
        logger.warning(
            f"Filename {filename} does not match expected pattern. Skipping."
        )
        return False

    property_type, year, month = match.groups()

    # Create output filename and path
    output_filename = f"{property_type}_{year}_{month}.csv"
    output_path = os.path.join(output_dir, year, output_filename)

    # Skip if output file already exists
    if os.path.exists(output_path):
        logger.info(f"Output file {output_path} already exists. Skipping.")
        return True

    # Read and process PDF
    logger.info(f"Processing {pdf_path}")
    pdf_content = read_pdf_content(pdf_path)

    if not pdf_content:
        return False

    # Extract data using Gemini
    csv_content = extract_data_with_gemini(model, pdf_content, pdf_path)

    if not csv_content:
        return False

    # Save to CSV
    os.makedirs(os.path.join(output_dir, year), exist_ok=True)
    result = save_to_csv(csv_content, output_path)

    if result:
        logger.info(f"Successfully saved {output_path}")

    return result


def find_pdfs_for_single_type(base_dir, year, property_type):
    """Helper function to find PDFs for a single property type."""
    adjusted_property_type = property_type.upper()
    
    # Special handling for DETACHED to exclude DETACHED_CONDOMINIUM
    if adjusted_property_type == "DETACHED":
        # For DETACHED, we need to exclude DETACHED_CONDOMINIUM
        if year and year.lower() != "all":
            # Search in a specific year directory for all DETACHED files
            search_path = os.path.join(base_dir, year, f"{adjusted_property_type}*.pdf")
            all_files = glob.glob(search_path)
            # Filter out DETACHED_CONDOMINIUM files
            filtered_files = [f for f in all_files if "CONDOMINIUM" not in os.path.basename(f)]
        else:
            # Search in all year directories for all DETACHED files
            search_path = os.path.join(base_dir, "*", f"{adjusted_property_type}*.pdf")
            all_files = glob.glob(search_path)
            # Filter out DETACHED_CONDOMINIUM files
            filtered_files = [f for f in all_files if "CONDOMINIUM" not in os.path.basename(f)]
        
        return sorted(filtered_files)
    
    # Handle special cases
    if adjusted_property_type in ["SEMI-DETACHED", "TOWNHOUSE"]:
        # These might have additional text in the filename
        property_pattern = f"{adjusted_property_type}*"
    elif adjusted_property_type == "DETACHED_CONDOMINIUM":
        # Specific handling for DETACHED_CONDOMINIUM
        property_pattern = "DETACHED_CONDOMINIUM*"
    else:
        property_pattern = adjusted_property_type
    
    # Construct paths
    if year and year.lower() != "all":
        # Search in a specific year directory
        search_path = os.path.join(base_dir, year, f"{property_pattern}_*.pdf")
    else:
        # Search in all year directories
        search_path = os.path.join(base_dir, "*", f"{property_pattern}_*.pdf")
    
    # Find matching files and sort them
    matching_files = sorted(glob.glob(search_path))
    return matching_files


def find_pdfs(base_dir, year=None, property_type=None):
    """Find PDF files matching the specified criteria."""
    # Define the pattern based on inputs
    if year and year.lower() != "all":
        year_pattern = year
    else:
        year_pattern = "*"
    
    if property_type and property_type.upper() != "ALL":
        # Handle special cases where property_type needs adjustment
        adjusted_property_type = property_type.upper()
        
        # Handle comma-separated property types
        if "," in adjusted_property_type:
            logger.warning(
                "Multiple property types detected in the legacy method. Use --property_types instead."
            )
            property_types = [pt.strip() for pt in adjusted_property_type.split(",")]
            all_files = []
            for pt in property_types:
                files = find_pdfs_for_single_type(base_dir, year, pt)
                all_files.extend(files)
            # Sort files by name
            return sorted(all_files)
        
        # Handle single property type
        return find_pdfs_for_single_type(base_dir, year, adjusted_property_type)
    else:
        # Process all property types
        property_pattern = "*"
        
        # Construct paths
        if year and year.lower() != "all":
            # Search in a specific year directory
            search_path = os.path.join(base_dir, year, f"{property_pattern}_*.pdf")
        else:
            # Search in all year directories
            search_path = os.path.join(base_dir, "*", f"{property_pattern}_*.pdf")
        
        # Find matching files and sort them
        matching_files = sorted(glob.glob(search_path))

    # If no files found with the pattern, try to identify why
    if not matching_files:
        logger.warning(f"No files found matching pattern: {search_path}")
        if year and year.lower() != "all":
            if year not in AVAILABLE_YEARS:
                logger.error(
                    f"Invalid year: {year}. Available years: {', '.join(AVAILABLE_YEARS)}"
                )
            else:
                # Check if the year directory exists
                year_dir = os.path.join(base_dir, year)
                if not os.path.exists(year_dir):
                    logger.error(f"Year directory not found: {year_dir}")
                else:
                    logger.info(
                        f"Year directory exists but no matching files for property type: {property_type}"
                    )

        if property_type and property_type.upper() != "ALL":
            if property_type.upper() not in [
                pt.replace("_", "") for pt in PROPERTY_TYPES
            ]:
                logger.error(
                    f"Invalid property type: {property_type}. Available types: {', '.join(PROPERTY_TYPES)}"
                )

    return matching_files


def main():
    """Main function to process PDFs to CSVs based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert TRREB PDF reports to CSV files"
    )
    parser.add_argument(
        "--years",
        type=str,
        default="all",
        help='Years to process (e.g., "2024", "2022,2023,2024", "all")',
    )
    parser.add_argument(
        "--property_types",
        type=str,
        default="ALL",
        help='Property types to process (e.g., "ALL_HOME", "DETACHED,CONDO_APT,TOWNHOUSE", "ALL")',
    )
    parser.add_argument(
        "--api_key", type=str, required=True, help="Google Gemini API key"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=OUTPUT_DIR,
        help="Output directory for CSV files",
    )

    # For backward compatibility
    parser.add_argument(
        "--year", type=str, help="Legacy: Year to process (use --years instead)"
    )
    parser.add_argument(
        "--property_type",
        type=str,
        help="Legacy: Property type to process (use --property_types instead)",
    )

    args = parser.parse_args()

    # Handle legacy parameters for backward compatibility
    if args.year and not args.years:
        args.years = args.year
        logger.warning("--year is deprecated, use --years instead")

    if args.property_type and not args.property_types:
        args.property_types = args.property_type
        logger.warning("--property_type is deprecated, use --property_types instead")

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Setup Gemini API
    model = setup_gemini_api(args.api_key)

    # Parse multiple years
    if args.years.lower() == "all":
        years_to_process = ["all"]
    else:
        years_to_process = [year.strip() for year in args.years.split(",")]

    # Parse multiple property types
    if args.property_types.upper() == "ALL":
        property_types_to_process = ["ALL"]
    else:
        property_types_to_process = [
            prop_type.strip().upper() for prop_type in args.property_types.split(",")
        ]

    all_pdf_files = []

    # Find PDFs for each combination of year and property type
    for year in years_to_process:
        for property_type in property_types_to_process:
            pdf_files = find_pdfs(PDF_DIR, year, property_type)
            all_pdf_files.extend(pdf_files)

    # Remove duplicates (in case of overlapping criteria)
    all_pdf_files = list(set(all_pdf_files))
    
    # Sort the file list for consistent processing order
    all_pdf_files.sort()

    if not all_pdf_files:
        logger.error("No PDF files found matching the specified criteria")
        return

    # Log sorted list of PDF files for debugging
    logger.info(f"Found {len(all_pdf_files)} PDF files to process")
    if len(all_pdf_files) <= 10:  # Only log all filenames if there are few files
        for pdf_file in all_pdf_files:
            logger.info(f"  - {os.path.basename(pdf_file)}")
    else:
        # Log first 5 and last 5 files if there are many
        logger.info("First 5 files:")
        for pdf_file in all_pdf_files[:5]:
            logger.info(f"  - {os.path.basename(pdf_file)}")
        logger.info("Last 5 files:")
        for pdf_file in all_pdf_files[-5:]:
            logger.info(f"  - {os.path.basename(pdf_file)}")

    # Process each PDF
    success_count = 0
    for pdf_path in all_pdf_files:
        if process_pdf(model, pdf_path, args.output_dir):
            success_count += 1

    logger.info(
        f"Processed {success_count} of {len(all_pdf_files)} PDF files successfully"
    )


if __name__ == "__main__":
    main()
