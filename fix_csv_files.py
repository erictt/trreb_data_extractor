#!/usr/bin/env python3
"""
Fix CSV Files

This script cleans up CSV files generated from Gemini API responses by removing
Markdown formatting markers and ensuring proper CSV format.
"""

import os
import glob
import argparse
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("fix_csv_files.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

def clean_column_headers(content):
    """Clean column headers by removing superscript notations and standardizing names."""
    if not content:
        return content
    
    lines = content.split('\n')
    if not lines:
        return content
    
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

def clean_csv_content(content):
    """Clean CSV content by removing Markdown formatting and cleaning headers."""
    cleaned = content
    
    # Remove Markdown code block markers at the beginning
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline > 0:
            cleaned = cleaned[first_newline + 1:]
    
    # Remove trailing Markdown code block markers
    if cleaned.strip().endswith("```"):
        cleaned = cleaned.strip()[:-3].strip()
    
    # Clean column headers
    cleaned = clean_column_headers(cleaned)
    
    return cleaned

def fix_csv_file(file_path):
    """Fix a single CSV file by removing Markdown formatting."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it has Markdown formatting
        # Check if any headers have superscript numbers or need standardization
        headers = content.split('\n')[0].split(',')
        needs_fixing = (
            content.startswith("```") or 
            content.strip().endswith("```") or 
            any(re.search(r'\b\w+\s+\d+\b', header) for header in headers) or
            any(re.search(r'\bAvg\.\s*SP\s*/\s*LP\b', header) for header in headers) or
            any(re.search(r'\bMos\.\s*Inv\.\b', header) for header in headers) or
            any(re.search(r'\b#\s*of\s*Sales\b', header) for header in headers)
        )
        
        if needs_fixing:
            # Clean the content
            cleaned_content = clean_csv_content(content)
            
            # Write back to the file
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(cleaned_content)
            
            logger.info(f"Fixed Markdown formatting in {file_path}")
            return True
        else:
            logger.info(f"No issues found in {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def fix_csv_files(base_dir, year=None):
    """Fix all CSV files in the specified directory structure."""
    # Determine search path
    if year:
        search_path = os.path.join(base_dir, year, "*.csv")
    else:
        search_path = os.path.join(base_dir, "*", "*.csv")
    
    # Find all CSV files
    csv_files = sorted(glob.glob(search_path))
    logger.info(f"Found {len(csv_files)} CSV files to check")
    
    # Process each file
    fixed_count = 0
    for file_path in csv_files:
        if fix_csv_file(file_path):
            fixed_count += 1
    
    logger.info(f"Fixed {fixed_count} of {len(csv_files)} CSV files")
    return fixed_count

def main():
    """Main function to fix CSV files based on command line arguments."""
    parser = argparse.ArgumentParser(description='Fix CSV files by removing Markdown formatting')
    parser.add_argument(
        '--year',
        type=str,
        help='Specific year to process (e.g., "2016"). If not provided, all years will be processed.',
    )
    parser.add_argument(
        '--dir',
        type=str,
        default="/Users/eric/workspace/mcp/trreb_data_extractor/csv-outputs",
        help='Base directory containing CSV files',
    )
    
    args = parser.parse_args()
    
    # Fix CSV files
    fix_csv_files(args.dir, args.year)

if __name__ == "__main__":
    main()
