#!/usr/bin/env python3
"""
Enhanced script to extract TRREB Areas summary pages from Market Watch PDFs.

This script:
1. Extracts only pages with ALL TRREB AREAS data
   (avoids City of Toronto Municipal Breakdown pages)
2. Renames "ROW" property type to "TOWNHOUSE" for consistency
3. Uses numeric month format (01, 02, etc.) in filenames
4. Works with all formats of TRREB reports (2016-2024)
5. Supports extracting data for a specific year
6. Fixes issues with Year-to-Date data incorrectly identified as ALL_HOME_TYPES
7. Improves pattern matching for CONDO APT detection

Usage:
    python trreb_areas_extract.py [--year YYYY] [--include-ytd] [--debug]
"""

import os
import re
import pdfplumber
from datetime import datetime
import logging
from PyPDF2 import PdfWriter, PdfReader
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trreb_areas_extract.log"),
        logging.StreamHandler(),
    ],
)


def extract_date_from_filename(filename):
    """Extract year and month from filename format 'mwYYMM.pdf'"""
    match = re.match(r"mw(\d{2})(\d{2})\.pdf", os.path.basename(filename))
    if not match:
        return None

    yy, mm = match.groups()
    year = 2000 + int(yy)
    month = int(mm)

    return datetime(year, month, 1)


def determine_property_type_from_text(text):
    """
    Determine property type from page text using optimized pattern matching
    """
    # Enhanced patterns for CONDO APT - check first as these can be tricky
    condo_apt_patterns = [
        r"\bCONDO\s*APT\b", 
        r"\bCONDOMINIUM\s*APARTMENT\b",
        r"\bAPARTMENT\s*CONDOMINIUM\b",
        r"\bCONDO\s*APARTMENT\b"
    ]
    
    for pattern in condo_apt_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "CONDO APT"
    
    # Look for title-based identification (most reliable)
    if "SEMI-DETACHED HOUSES" in text.upper():
        return "SEMI-DETACHED"
    elif "DETACHED HOUSES" in text.upper() and "SEMI-DETACHED" not in text.upper():
        return "DETACHED"
    elif "DETACHED CONDOMINIUM" in text.upper() or "DETACHED CONDO" in text.upper():
        return "DETACHED CONDOMINIUM"
    elif "CONDO TOWNHOUSE" in text.upper() or "CONDOMINIUM TOWNHOUSE" in text.upper():
        return "CONDO TOWNHOUSE"
    elif "TOWNHOUSE" in text.upper() and "CONDO" not in text.upper():
        return "TOWNHOUSE"
    elif "ALL HOME TYPES" in text.upper() and "YEAR-TO-DATE" not in text.upper():
        return "ALL HOME TYPES"
    
    # Fallback to pattern matching if title-based identification fails
    property_patterns = [
        # Exact property type phrases that might appear in the text
        (r"\bALL HOME TYPES\b", "ALL HOME TYPES"),
        (r"\bCONDO TOWNHOUSE\b", "CONDO TOWNHOUSE"),  # Check this before TOWNHOUSE
        (r"\bTOWNHOUSE\b(?!.*CONDO)", "TOWNHOUSE"),
        (
            r"\bDETACHED CONDOMINIUM\b",
            "DETACHED CONDOMINIUM",
        ),  # Check this before regular DETACHED
        (r"\bDETACHED CONDO\b", "DETACHED CONDOMINIUM"),  # Another way it might appear
        (r"\bDETACHED HOUSES\b", "DETACHED"),  # Explicit DETACHED HOUSES
        (
            r"\bDETACHED\b(?!.*SEMI)(?!.*CONDO)",
            "DETACHED",
        ),  # DETACHED but not SEMI-DETACHED or DETACHED CONDOMINIUM
        (r"\bSEMI-DETACHED HOUSES\b", "SEMI-DETACHED"),  # Explicit SEMI-DETACHED HOUSES
        (r"\bSEMI-DETACHED\b", "SEMI-DETACHED"),
        (r"\bROW\b", "TOWNHOUSE"),  # Rename ROW to TOWNHOUSE
        (r"\bATTACHED\b", "ATTACHED"),
    ]

    # Check for each pattern in the text
    for pattern, prop_type in property_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return prop_type

    # If we get here, we couldn't determine the property type
    return None


def is_trreb_areas_page(text, page_num, filename):
    """
    Determines if this is a TRREB Areas summary page
    (as opposed to a City of Toronto Municipal Breakdown page)
    
    Returns a tuple: (is_trreb_page, is_year_to_date)
    """
    # First check if it's a summary page
    if "SUMMARY OF EXISTING HOME TRANSACTIONS" not in text:
        return False, False
    
    # Check if it's a YEAR-TO-DATE report
    is_year_to_date = "YEAR-TO-DATE" in text or "Year-to-Date" in text

    # Check for ALL TREB/TRREB AREAS indicators (in the title or in the data table)
    is_all_trreb_areas = any(
        x in text
        for x in [
            "ALL TRREB AREAS",
            "ALL TREB AREAS",
            "All TREB Areas",
            "All TRREB Areas",
        ]
    )
    
    # Special handling for "All Home Types" heading
    if "All Home Types" in text and not is_year_to_date:
        # Check if it's a municipal breakdown (which we want to skip)
        if "City of Toronto Municipal Breakdown" in text or "Municipal Breakdown" in text:
            logging.info(
                f"  Skipping municipal breakdown page {page_num + 1} in {filename}"
            )
            return False, False
    
    return is_all_trreb_areas, is_year_to_date


def determine_page_properties(text, date, page_num, filename):
    """
    Determine property type and if it's year-to-date from page text

    Returns: (property_type, is_year_to_date, page_title, filename)
    """
    # Check if it's a valid TRREB Areas page and if it's Year-to-Date
    is_trreb_page, is_year_to_date = is_trreb_areas_page(text, page_num, filename)
    
    if not is_trreb_page:
        return None, False, None, None
    
    # Determine property type using specialized function
    property_type = determine_property_type_from_text(text)
    
    # If no property type determined, return None
    if property_type is None:
        return None, False, None, None
    
    # Format month numerically (01, 02, etc.)
    month_number = f"{date.month:02d}"
    year = date.year
    
    # Create page title (for display in logs)
    if is_year_to_date:
        page_title = f"{property_type}, YEAR-TO-DATE {year}"
    else:
        page_title = f"{property_type}, {date.strftime('%B').upper()} {year}"
    
    # Create filename
    if is_year_to_date:
        clean_filename = f"{property_type.replace(' ', '_')}_YTD_{year}.pdf"
    else:
        clean_filename = f"{property_type.replace(' ', '_')}_{year}_{month_number}.pdf"
    
    return property_type, is_year_to_date, page_title, clean_filename


def debug_extract_text(pdf_path, page_num):
    """Debug function to extract and print text from a specific page"""
    with pdfplumber.open(pdf_path) as pdf:
        if page_num < len(pdf.pages):
            try:
                text = pdf.pages[page_num].extract_text()
                print(f"\nText from {pdf_path}, page {page_num + 1}:")
                print("=" * 80)
                print(text[:500] + "..." if len(text) > 500 else text)
                print("=" * 80)
                return text
            except Exception as e:
                print(
                    f"Error extracting text from {pdf_path}, page {page_num + 1}: {e}"
                )
    return None


def extract_and_save_summary_pages(
    pdf_dir="pdfs", 
    output_base_dir="split-pdfs", 
    include_ytd=False, 
    debug=False,
    specific_year=None
):
    """
    Extract ALL TRREB AREAS summary pages and save individually

    Args:
        pdf_dir: Directory containing TRREB PDF files
        output_base_dir: Base directory for output files
        include_ytd: Whether to include YEAR-TO-DATE pages (default: False)
        debug: Whether to enable extra debugging output
        specific_year: Optional specific year to extract (default: None = all years)
    """
    # Get all PDF files
    pdf_files = [
        os.path.join(pdf_dir, f)
        for f in os.listdir(pdf_dir)
        if f.endswith(".pdf") and f.startswith("mw")
    ]

    # Sort PDFs by date
    pdf_files.sort(key=extract_date_from_filename)

    # Filter by specific year if provided
    if specific_year:
        filtered_pdf_files = []
        for pdf_path in pdf_files:
            date = extract_date_from_filename(pdf_path)
            if date and date.year == specific_year:
                filtered_pdf_files.append(pdf_path)
        
        pdf_files = filtered_pdf_files
        
        if not pdf_files:
            logging.warning(f"No PDF files found for year {specific_year}")
            print(f"No PDF files found for year {specific_year}")
            return 0, 0, 0, 0, set()
        
        logging.info(f"Filtered to {len(pdf_files)} PDF files for year {specific_year}")

    # Track statistics
    total_pdfs = len(pdf_files)
    total_pages = 0
    saved_pages = 0
    skipped_ytd = 0
    skipped_municipal = 0

    # Track property types by year/month
    property_by_date = {}

    # Process each PDF
    for pdf_path in pdf_files:
        try:
            filename = os.path.basename(pdf_path)
            date = extract_date_from_filename(pdf_path)
            if not date:
                logging.warning(f"Could not extract date from {pdf_path}, skipping")
                continue

            year = date.year
            month = date.month
            month_year = date.strftime("%b %Y")

            # Initialize tracking for this date
            date_key = f"{year}-{month:02d}"
            if date_key not in property_by_date:
                property_by_date[date_key] = {"found": set(), "file": filename}

            # Create output directory for this year
            output_dir = os.path.join(output_base_dir, str(year))
            os.makedirs(output_dir, exist_ok=True)

            logging.info(f"Processing {month_year} - {pdf_path}")

            # Special debug for files
            if debug:
                logging.info(f"Debugging {month_year} ({filename})...")
                # Look at first few pages for analysis
                for i in range(min(10, len(PdfReader(pdf_path).pages))):
                    debug_extract_text(pdf_path, i)

            # Using pdfplumber for better text extraction
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                total_pages += page_count

                # Process each page
                for i, page in enumerate(pdf.pages):
                    try:
                        # Extract text from the page
                        text = page.extract_text()

                        # Determine if this is a relevant summary page
                        props = determine_page_properties(text, date, i, filename)
                        if props[0] is None:
                            continue  # Skip non-summary pages

                        property_type, is_year_to_date, page_title, filename_out = props

                        # Track property types found for this month (only for non-YTD)
                        if not is_year_to_date:
                            property_by_date[date_key]["found"].add(property_type)

                        # Skip year-to-date pages if not requested
                        if is_year_to_date and not include_ytd:
                            logging.info(
                                f"  Skipping YEAR-TO-DATE page {i + 1}: {page_title}"
                            )
                            skipped_ytd += 1
                            continue

                        # Generate output path
                        output_path = os.path.join(output_dir, filename_out)

                        # We need to use PyPDF2 to save the page
                        pdf_reader = PdfReader(pdf_path)
                        output = PdfWriter()
                        output.add_page(pdf_reader.pages[i])

                        # Save the page
                        with open(output_path, "wb") as f:
                            output.write(f)

                        saved_pages += 1
                        logging.info(
                            f"  Saved page {i + 1}/{page_count}: {page_title} to {output_path}"
                        )

                    except Exception as e:
                        logging.error(
                            f"Error processing page {i + 1} in {pdf_path}: {e}"
                        )

        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")

    # Analyze property types across the dataset
    all_property_types = set()
    for date_data in property_by_date.values():
        all_property_types.update(date_data["found"])

    # Check for missing property types by date
    missing_analysis = []
    expected_types = [
        "ALL HOME TYPES",
        "DETACHED",
        "SEMI-DETACHED",
        "CONDO APT",
        "TOWNHOUSE",
        "CONDO TOWNHOUSE",
    ]

    for date_key, data in sorted(property_by_date.items()):
        year, month = date_key.split("-")
        missing = [p for p in expected_types if p not in data["found"]]
        if missing:
            missing_analysis.append(
                {
                    "date": f"{year}-{month}",
                    "file": data["file"],
                    "missing": missing,
                    "found": list(data["found"]),
                }
            )

    # Print summary
    year_str = f" for {specific_year}" if specific_year else ""
    logging.info(
        f"Completed processing {total_pdfs} PDFs{year_str} with {total_pages} total pages"
    )
    logging.info(f"Saved {saved_pages} summary pages to {output_base_dir}")
    if skipped_ytd > 0:
        logging.info(
            f"Skipped {skipped_ytd} YEAR-TO-DATE pages (include_ytd={include_ytd})"
        )
    if skipped_municipal > 0:
        logging.info(f"Skipped {skipped_municipal} municipal breakdown pages")

    print(f"\nProperty Types Found{year_str} ({len(all_property_types)}):")
    for prop_type in sorted(all_property_types):
        print(f"  - {prop_type}")

    print(f"\nMissing Property Type Analysis:")
    if missing_analysis:
        for item in missing_analysis:
            print(
                f"  {item['date']} ({item['file']}): Missing {', '.join(item['missing'])}"
            )
    else:
        print("  No missing property types detected!")

    return total_pdfs, total_pages, saved_pages, skipped_ytd, all_property_types


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Extract TRREB Areas summary pages from Market Watch PDFs"
    )
    
    parser.add_argument(
        "--year", 
        type=int, 
        help="Specific year to extract (e.g., 2020)"
    )
    
    parser.add_argument(
        "--include-ytd", 
        action="store_true", 
        help="Include YEAR-TO-DATE pages in the extraction"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode with additional output"
    )
    
    parser.add_argument(
        "--pdf-dir",
        default="pdfs",
        help="Directory containing the PDF files (default: pdfs)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="split-pdfs",
        help="Base directory for output files (default: split-pdfs)"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Set to True if you want to include YEAR-TO-DATE pages
    total_pdfs, total_pages, saved_pages, skipped_ytd, property_types = (
        extract_and_save_summary_pages(
            pdf_dir=args.pdf_dir,
            output_base_dir=args.output_dir,
            include_ytd=args.include_ytd, 
            debug=args.debug,
            specific_year=args.year
        )
    )

    year_str = f" for {args.year}" if args.year else ""
    print(f"\nSummary{year_str}:")
    print(f"Processed {total_pdfs} PDF files with {total_pages} total pages")
    print(
        f"Extracted and saved {saved_pages} individual 'SUMMARY OF EXISTING HOME TRANSACTIONS' pages"
    )
    print(f"Skipped {skipped_ytd} YEAR-TO-DATE pages")
    print(f"Found {len(property_types)} distinct property types")
    
    if args.year:
        print(f"Files are saved in {args.output_dir}/{args.year}/ with numeric month format (e.g., DETACHED_{args.year}_07.pdf)")
    else:
        print(f"Files are saved in {args.output_dir}/<year>/ with numeric month format (e.g., DETACHED_2020_07.pdf)")
