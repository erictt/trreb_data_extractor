#!/usr/bin/env python3
"""
TRREB Table Extractor - Simplified version using only tabula-py

This script extracts tables from TRREB PDF reports and converts them to standardized CSV format,
handling different formats across years (pre-2020 and post-2020).
"""

import os
import pandas as pd
import tabula
import PyPDF2
import re
from pathlib import Path
import warnings

# Suppress annoying pandas warnings
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Define paths
BASE_DIR = Path("./")
PDF_DIR = BASE_DIR / "extracted_data"
ALL_HOMES_DIR = PDF_DIR / "all_home_types"
DETACHED_DIR = PDF_DIR / "detached"
CSV_DIR = BASE_DIR / "csv_data"
ALL_HOMES_CSV_DIR = CSV_DIR / "all_home_types"
DETACHED_CSV_DIR = CSV_DIR / "detached"

# Create output directories
for dir_path in [CSV_DIR, ALL_HOMES_CSV_DIR, DETACHED_CSV_DIR]:
    os.makedirs(dir_path, exist_ok=True)


def extract_date_from_pdf(pdf_path):
    """
    Extract the date (month and year) from the content of the PDF or filename.
    """
    with open(pdf_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = pdf_reader.pages[0].extract_text()

        # Look for common date formats in the PDF
        # Try to find month and year in the format "Month YYYY"
        month_year_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
        match = re.search(month_year_pattern, text)
        if match:
            month, year = match.groups()
            month_num = {
                "January": "01",
                "February": "02",
                "March": "03",
                "April": "04",
                "May": "05",
                "June": "06",
                "July": "07",
                "August": "08",
                "September": "09",
                "October": "10",
                "November": "11",
                "December": "12",
            }[month]
            return f"{year}-{month_num}"


def identify_municipalities(df):
    """
    Identify the column or row containing municipality names and transform if needed.
    Returns a cleaned DataFrame with municipalities as index or first column.
    """
    if df is None or df.empty:
        return None

    # Common municipalities to look for
    key_municipalities = [
        "TREB Total",
        "TRREB Total",
        "Halton Region",
        "Peel Region",
        "City of Toronto",
        "York Region",
        "Durham Region",
    ]

    # Check if municipalities are in the first column
    if df.shape[1] > 0:
        first_col = df.iloc[:, 0].astype(str)
        if any(muni in " ".join(first_col.values) for muni in key_municipalities):
            return df

    # If municipalities are not in the first column, check other columns
    for col in range(1, min(df.shape[1], 3)):  # Check first few columns
        col_values = df.iloc[:, col].astype(str)
        if any(muni in " ".join(col_values.values) for muni in key_municipalities):
            # Move this column to the first position
            cols = list(df.columns)
            cols.insert(0, cols.pop(col))
            return df[cols]

    # If municipalities are in rows rather than columns, transpose the DataFrame
    for row in range(min(df.shape[0], 5)):  # Check first few rows
        row_values = df.iloc[row, :].astype(str)
        if any(muni in " ".join(row_values.values) for muni in key_municipalities):
            # Use this row as the header
            new_header = df.iloc[row]
            df = df.iloc[row + 1 :]
            df.columns = new_header
            return df

    return df  # Return original if we couldn't identify municipalities


def clean_table(df, report_type):
    """Clean and format the extracted table data."""
    if df is None or df.empty:
        return None

    # Try to identify the data table structure
    df = identify_municipalities(df)

    # Remove rows where all values are NaN
    df = df.dropna(how="all")

    # For rows, try to identify if the first row is actually column headers
    if df.shape[0] > 0:
        first_row = df.iloc[0].astype(str)
        if any(
            col.lower() in " ".join(first_row.values).lower()
            for col in ["sales", "average price", "new listings", "active"]
        ):
            # First row appears to be headers
            new_headers = df.iloc[0]
            df = df.iloc[1:]
            df.columns = new_headers

            # Reapply column name cleaning
            df.columns = [
                str(col).strip().replace("\n", " ").replace("\r", "")
                for col in df.columns
            ]
            df.columns = [re.sub(r"\s+", " ", col) for col in df.columns]

    # Remove any unwanted rows based on specific patterns
    unwanted_patterns = ["Source:", "Notes:", "Copyright", "© 20", "Market Watch"]
    for pattern in unwanted_patterns:
        if "Municipality" in df.columns:
            df = df[~df["Municipality"].astype(str).str.contains(pattern, na=False)]
        else:
            # If no Municipality column, check the first column
            first_col = df.columns[0]
            df = df[~df[first_col].astype(str).str.contains(pattern, na=False)]

    # Try to convert numeric columns
    numeric_cols = [
        "Sales",
        "Dollar Volume",
        "Average Price",
        "Median Price",
        "New Listings",
        "Active Listings",
        "Avg. DOM",
    ]

    for col in numeric_cols:
        if col in df.columns:
            try:
                # Remove $ and , characters for price columns
                if any(x in col for x in ["Price", "Volume"]):
                    df[col] = df[col].astype(str).str.replace("$", "", regex=False)
                    df[col] = df[col].astype(str).str.replace(",", "", regex=False)

                # Convert to numeric
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except:
                pass

    # Handle percentage columns
    pct_cols = ["Avg. SP/LP", "SNLR (Trend)"]
    for col in pct_cols:
        if col in df.columns:
            try:
                df[col] = df[col].astype(str).str.replace("%", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except:
                pass

    # Replace NaN in the first column header with 'Municipality'
    if pd.isna(df.columns[0]) or df.columns[0] == "":
        df.columns = ["Municipality"] + list(df.columns[1:])

    # Remove empty trailing columns (columns where all values are NaN)
    df = df.dropna(axis=1, how="all")

    # Remove any rows that contain footnote markers
    if df.shape[1] > 0 and "Municipality" in df.columns:
        # Remove rows where Municipality is just a number
        df = df[~df["Municipality"].astype(str).str.match(r"^\d+$", na=False)]
        # Remove summary or footnote rows
        footnote_patterns = ["SUMMARY OF", "Copyright", "Source:", "Notes:", "© 20"]
        for pattern in footnote_patterns:
            df = df[
                ~df["Municipality"]
                .astype(str)
                .str.contains(pattern, na=False, case=False)
            ]

    # remove the last row with the first cell of number 3
    df = df[~df.iloc[:, 0].astype(str).str.match(r"^\d+$", na=False)]

    return df


def extract_tabula_tables(pdf_path, report_type):
    """Extract tables using tabula with different strategies."""
    tables = []

    # Try with area detection
    try:
        # First try with lattice=True (for tables with lines/borders)
        tables = tabula.read_pdf(
            pdf_path, pages="1", multiple_tables=True, lattice=True
        )

        # If no tables or small tables found, try with stream=True
        if not tables or all(t.shape[0] < 5 for t in tables if not t.empty):
            tables = tabula.read_pdf(
                pdf_path, pages="1", multiple_tables=True, lattice=False, stream=True
            )

        # Select the largest table
        if tables:
            largest_table = max(
                tables, key=lambda t: t.shape[0] * t.shape[1] if not t.empty else 0
            )
            return largest_table
    except Exception as e:
        print(f"Error extracting tables with tabula: {e}")

    return None


def process_pdf(pdf_path, output_path, report_type):
    """Extract table from PDF and save as CSV."""
    # Extract tables using tabula
    df = extract_tabula_tables(pdf_path, report_type)

    # Clean and standardize the table
    if df is not None and not df.empty:
        df = clean_table(df, report_type)
        df.to_csv(output_path, index=False)
        print(f"  ✓ Saved table to {output_path}")
        return True, df.shape
    else:
        print(f"  ✗ Failed to extract table from {pdf_path}")
        return False, (0, 0)


def process_all_pdfs():
    """Process all PDF files in the extracted data directories."""
    all_homes_results = []
    detached_results = []

    # Process ALL HOME TYPES PDFs
    all_homes_files = sorted(
        [f for f in os.listdir(ALL_HOMES_DIR) if f.lower().endswith(".pdf")]
    )

    all_homes_files = list(filter(lambda x: x < "2020-01", all_homes_files))

    print(f"\nProcessing {len(all_homes_files)} ALL HOME TYPES PDFs...")
    for pdf_file in all_homes_files:
        pdf_path = ALL_HOMES_DIR / pdf_file
        date_str = extract_date_from_pdf(pdf_path)
        output_path = ALL_HOMES_CSV_DIR / f"{date_str}.csv"

        print(f"Processing ALL HOME TYPES: {pdf_file} (Date: {date_str})...")
        success, shape = process_pdf(pdf_path, output_path, "all_home_types")

        all_homes_results.append(
            {
                "filename": pdf_file,
                "date": date_str,
                "success": success,
                "num_rows": shape[0],
                "num_cols": shape[1],
            }
        )

    # Process DETACHED PDFs
    detached_files = sorted(
        [f for f in os.listdir(DETACHED_DIR) if f.lower().endswith(".pdf")]
    )

    detached_files = list(filter(lambda x: x < "2020-01", detached_files))

    print(f"\nProcessing {len(detached_files)} DETACHED PDFs...")
    for pdf_file in detached_files:
        pdf_path = DETACHED_DIR / pdf_file
        date_str = extract_date_from_pdf(pdf_path)
        output_path = DETACHED_CSV_DIR / f"{date_str}.csv"

        print(f"Processing DETACHED: {pdf_file} (Date: {date_str})...")
        success, shape = process_pdf(pdf_path, output_path, "detached")

        detached_results.append(
            {
                "filename": pdf_file,
                "date": date_str,
                "success": success,
                "num_rows": shape[0],
                "num_cols": shape[1],
            }
        )

    # Print statistics
    total_all_homes = len(all_homes_results)
    successful_all_homes = sum(1 for r in all_homes_results if r["success"])

    total_detached = len(detached_results)
    successful_detached = sum(1 for r in detached_results if r["success"])

    print(f"\nStatistics:")
    print(
        f"ALL HOME TYPES: {successful_all_homes}/{total_all_homes} successful ({successful_all_homes / total_all_homes * 100:.1f}%)"
    )
    print(
        f"DETACHED: {successful_detached}/{total_detached} successful ({successful_detached / total_detached * 100:.1f}%)"
    )


if __name__ == "__main__":
    process_all_pdfs()
