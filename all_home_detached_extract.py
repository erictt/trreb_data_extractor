#!/usr/bin/env python3
"""
TRREB Data Extractor

This script extracts specific pages from Toronto Regional Real Estate Board (TRREB)
PDF reports, specifically "ALL HOME TYPES" and "DETACHED" pages.
"""

import os
import re
import PyPDF2
import pandas as pd
from datetime import datetime
from pathlib import Path

# Define paths
BASE_DIR = Path("/Users/eric/workspace/mcp/trreb_data_extractor")
PDF_DIR = BASE_DIR / "pdfs"
OUTPUT_DIR = BASE_DIR / "extracted_data"

# Create output directories
ALL_HOMES_DIR = OUTPUT_DIR / "all_home_types"
DETACHED_DIR = OUTPUT_DIR / "detached"

os.makedirs(ALL_HOMES_DIR, exist_ok=True)
os.makedirs(DETACHED_DIR, exist_ok=True)


def extract_date_from_filename(filename):
    """Extract the date from the filename if possible."""
    # Handle the common TRREB naming format: mwYYMM.pdf
    mw_pattern = r"mw(\d{2})(\d{2})\.pdf"
    match = re.match(mw_pattern, filename.lower())
    if match:
        year, month = match.groups()
        # Adjust for 2-digit year format
        if int(year) >= 0 and int(year) <= 99:
            if int(year) <= 25:  # Assuming current reports up to 2025
                year = f"20{year}"
            else:
                year = f"19{year}"
        return f"{year}-{month}"

    # Try other common patterns
    date_patterns = [
        r"(\d{4})[-_]?(\d{1,2})",  # YYYY-MM or YYYY_MM
        r"(\w+)[-_]?(\d{4})",  # Month-YYYY or Month_YYYY
    ]

    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                if groups[0].isdigit() and groups[1].isdigit():
                    # YYYY-MM format
                    return f"{groups[0]}-{groups[1].zfill(2)}"
                else:
                    # Month-YYYY format
                    month_str = groups[0]
                    year_str = groups[1]
                    try:
                        month_num = datetime.strptime(month_str[:3], "%b").month
                        return f"{year_str}-{str(month_num).zfill(2)}"
                    except ValueError:
                        pass

    # If no date found in filename, return None
    return None


def identify_page_types(pdf_path):
    """
    Identify the page numbers for "ALL HOME TYPES" and "DETACHED" sections.
    Returns a dictionary with keys 'all_home_types' and 'detached' containing the page numbers.
    """
    result = {"all_home_types": None, "detached": None}

    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            # Patterns to search for (expanded for more formats)
            all_homes_patterns = [
                r"(ALL HOME TYPES,|SUMMARY OF EXISTING HOME TRANSACTIONS All Home Types)",
                r"SUMMARY OF EXISTING HOME TRANSACTIONS ALL TRREB AREAS",
                r"SUMMARY OF EXISTING HOME TRANSACTIONS ALL TREB AREAS",
            ]

            detached_patterns = [
                r"(DETACHED,|SUMMARY OF EXISTING HOME TRANSACTIONS Detached)",
                r"SUMMARY OF EXISTING HOME TRANSACTIONS DETACHED",
                r"DETACHED, [A-Z]+ \d{4}",
                r"SUMMARY OF SALES AND AVERAGE PRICE BY MAJOR HOME TYPE, DETACHED",
            ]

            # Log all page titles for debugging
            page_titles = []

            # Iterate through pages to find matching sections
            for page_num in range(min(num_pages, 30)):  # Limit to first 30 pages
                try:
                    page_text = pdf_reader.pages[page_num].extract_text()
                    # Store first few lines of each page for logging
                    first_lines = " | ".join(page_text.split("\n")[:3])
                    page_titles.append(f"Page {page_num + 1}: {first_lines[:300]}")

                    # Check for ALL HOME TYPES patterns
                    if result["all_home_types"] is None:
                        for pattern in all_homes_patterns:
                            if re.search(pattern, page_text, re.IGNORECASE):
                                if (
                                    "ALL TRREB AREAS" in page_text
                                    or "ALL TREB AREAS" in page_text
                                ):
                                    result["all_home_types"] = page_num
                                    break

                    # Check for DETACHED patterns
                    if result["detached"] is None:
                        for pattern in detached_patterns:
                            if re.search(pattern, page_text, re.IGNORECASE):
                                if (
                                    "ALL TRREB AREAS" in page_text
                                    or "ALL TREB AREAS" in page_text
                                ):
                                    result["detached"] = page_num
                                    break
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
                    continue

            # Fall back to table-based identification for older reports
            if result["detached"] is None:
                for page_num in range(min(num_pages, 30)):
                    try:
                        page_text = pdf_reader.pages[page_num].extract_text()

                        # Check if it's a sales by property type page
                        if (
                            "DETACHED" in page_text
                            and "SALES" in page_text.upper()
                            and "AVERAGE PRICE" in page_text.upper()
                        ):
                            # Look for distinctive patterns that indicate this is the main detached page
                            if (
                                "ALL TREB AREAS" in page_text
                                or "ALL TRREB AREAS" in page_text
                            ):
                                result["detached"] = page_num
                                break

                        # For older reports (2016-2019), look for pages with "Detached" in the title
                        if (
                            "SUMMARY OF EXISTING HOME TRANSACTIONS" in page_text.upper()
                            and "DETACHED" in page_text.upper()
                        ):
                            result["detached"] = page_num
                            break
                    except Exception as e:
                        continue

            # Write page titles to file for debugging
            with open(OUTPUT_DIR / "page_titles.txt", "a") as f:
                f.write(f"\n\n--- {os.path.basename(pdf_path)} ---\n")
                f.write("\n".join(page_titles))

    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")

    return result


def extract_page_as_pdf(pdf_path, page_num, output_path):
    """Extract a specific page as a new PDF file."""
    if page_num is None:
        return False

    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if page_num >= len(pdf_reader.pages):
                return False

            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num])

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "wb") as output_file:
                pdf_writer.write(output_file)

        return True
    except Exception as e:
        print(f"Error extracting page {page_num} from {pdf_path}: {e}")
        return False


def process_all_pdfs():
    """Process all PDF files in the PDFs directory."""
    results = []

    # Get all PDF files
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])

    for pdf_file in pdf_files:
        pdf_path = PDF_DIR / pdf_file

        # Get date from filename
        date_str = extract_date_from_filename(pdf_file)
        if not date_str:
            # Use original filename as fallback
            print(
                f"⚠️ Could not extract date from {pdf_file}. Using filename as identifier."
            )
            date_str = os.path.splitext(pdf_file)[0]

        # Create base filename from original PDF (without extension)
        base_filename = os.path.splitext(pdf_file)[0]

        print(f"Processing {pdf_file} (Date: {date_str})...")

        # Identify page types
        page_info = identify_page_types(pdf_path)

        # Extract and save pages with unique filenames to type-specific folders
        all_homes_extracted = False
        detached_extracted = False

        if page_info["all_home_types"] is not None:
            all_homes_path = ALL_HOMES_DIR / f"{date_str}.pdf"
            all_homes_extracted = extract_page_as_pdf(
                pdf_path, page_info["all_home_types"], all_homes_path
            )
            if all_homes_extracted:
                print(
                    f"  ✓ ALL HOME TYPES page extracted to {os.path.basename(all_homes_path)}"
                )
            else:
                print(f"  ✗ Failed to extract ALL HOME TYPES page")
        else:
            print(f"  ✗ ALL HOME TYPES page not found")

        if page_info["detached"] is not None:
            detached_path = DETACHED_DIR / f"{date_str}.pdf"
            detached_extracted = extract_page_as_pdf(
                pdf_path, page_info["detached"], detached_path
            )
            if detached_extracted:
                print(
                    f"  ✓ DETACHED page extracted to {os.path.basename(detached_path)}"
                )
            else:
                print(f"  ✗ Failed to extract DETACHED page")
        else:
            print(f"  ✗ DETACHED page not found")

        # Add to results
        results.append(
            {
                "filename": pdf_file,
                "date": date_str,
                "all_home_types_page": page_info["all_home_types"],
                "all_home_types_extracted": all_homes_extracted,
                "detached_page": page_info["detached"],
                "detached_extracted": detached_extracted,
            }
        )

    # Create a summary DataFrame and save as CSV
    summary_df = pd.DataFrame(results)
    summary_path = OUTPUT_DIR / "extraction_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    print(f"\nExtraction complete! Summary saved to {summary_path}")

    # Print statistics
    total_pdfs = len(results)
    successful_all_homes = sum(1 for r in results if r["all_home_types_extracted"])
    successful_detached = sum(1 for r in results if r["detached_extracted"])

    print(f"Total PDFs processed: {total_pdfs}")
    print(
        f"Successfully extracted ALL HOME TYPES: {successful_all_homes}/{total_pdfs} ({successful_all_homes / total_pdfs * 100:.1f}%)"
    )
    print(
        f"Successfully extracted DETACHED: {successful_detached}/{total_pdfs} ({successful_detached / total_pdfs * 100:.1f}%)"
    )

    # Report on missing files
    missing_all_homes = [
        r["filename"] for r in results if not r["all_home_types_extracted"]
    ]
    missing_detached = [r["filename"] for r in results if not r["detached_extracted"]]

    if missing_all_homes:
        print("\nMissing ALL HOME TYPES pages in these files:")
        for filename in missing_all_homes[:10]:  # Show first 10
            print(f"  - {filename}")
        if len(missing_all_homes) > 10:
            print(f"  - ... and {len(missing_all_homes) - 10} more")

    if missing_detached:
        print("\nMissing DETACHED pages in these files:")
        for filename in missing_detached[:10]:  # Show first 10
            print(f"  - {filename}")
        if len(missing_detached) > 10:
            print(f"  - ... and {len(missing_detached) - 10} more")


if __name__ == "__main__":
    process_all_pdfs()
