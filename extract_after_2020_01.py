import pdftotext

import os
import argparse
from pathlib import Path
from openai import OpenAI

BASE_DIR = Path("./")
PDF_DIR = BASE_DIR / "extracted_data"
ALL_HOMES_DIR = PDF_DIR / "all_home_types"
DETACHED_DIR = PDF_DIR / "detached"
CSV_DIR = BASE_DIR / "csv_data"
ALL_HOMES_CSV_DIR = CSV_DIR / "all_home_types"
DETACHED_CSV_DIR = CSV_DIR / "detached"

# MODEL = "grok-3-latest"
MODEL = "grok-3-mini-fast-beta"

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)


def extract_page_text(pdf_path):
    with open(pdf_path, "rb") as f:
        doc = pdftotext.PDF(f)
    return doc[0]


def generate_prompt(text, source_name):
    if "2020-01" <= source_name <= "2022-04":
        return (
            """
    Construct a CSV file containing real estate transaction data for a specified month, using the provided PDF text in the <DATA> section below. The PDF text is structured similarly to the Toronto Regional Real Estate Board’s January 2020 report. The CSV must include the following columns: Region, # of Sales, Dollar Volume, Average Price, Median Price, New Listings, SNLR (Trend), Active Listings, Mos Inv (Trend), Avg. SP/LP, Avg. LDOM, Avg. PDOM. Adhere to the following formatting rules:

    1. The Region column should have no title in the CSV header (i.e., the first column header is empty).
    2. Extract data directly from the <DATA> section to populate the table, ensuring accuracy and completeness for the specified month indicated in the PDF text.
    3. Numeric values (e.g., # of Sales, New Listings, Active Listings) should be formatted without quotes unless they contain commas, in which case use double quotes.
    4. Monetary values (e.g., Dollar Volume, Average Price, Median Price) should include a dollar sign and commas for thousands (e.g., "$1,234,567") and be wrapped in quotes if commas are present.
    5. Percentage values (e.g., SNLR (Trend), Avg. SP/LP) should include a percent sign (e.g., "58.5%").
    6. Decimal values (e.g., Mos Inv (Trend)) should be formatted to one decimal place (e.g., "2.0").
    7. Wrap any field containing commas in double quotes to ensure proper CSV formatting.
    8. Preserve the hierarchical structure of regions (e.g., TREB Total, Halton Region, Burlington, etc.) as presented in the PDF text.

    **<DATA>**
    """
            + text
            + """
    **</DATA>**

    Respond ONLY with CSV content. Do not summarize or explain.
    """
        )
    else:
        return (
            """
    Construct a CSV file containing real estate transaction data for a specified month, using the provided PDF text in the `<DATA>` section below. The PDF text is structured similarly to the Toronto Regional Real Estate Board’s June 2024 report. The CSV must include the following columns: Region, Sales, Dollar Volume, Average Price, Median Price, New Listings, SNLR Trend, Active Listings, Mos Inv (Trend), Avg. SP/LP, Avg. LDOM, Avg. PDOM. Adhere to the following formatting rules:

    1. The Region column should have no title in the CSV header (i.e., the first column header is empty).
    2. Extract data directly from the `<DATA>` section to populate the table, ensuring accuracy and completeness for the specified month indicated in the PDF text.
    3. Numeric values (e.g., Sales, New Listings, Active Listings) should be formatted without quotes unless they contain commas, in which case use double quotes.
    4. Monetary values (e.g., Dollar Volume, Average Price, Median Price) should include a dollar sign and commas for thousands (e.g., "$1,234,567") and be wrapped in quotes if commas are present.
    5. Percentage values (e.g., SNLR Trend, Avg. SP/LP) should include a percent sign (e.g., "40.3%").
    6. Decimal values (e.g., Mos Inv (Trend)) should be formatted to one decimal place (e.g., "3.0").
    7. Wrap any field containing commas in double quotes to ensure proper CSV formatting.
    8. Preserve the hierarchical structure of regions (e.g., All TRREB Areas, Halton Region, Burlington, etc.) as presented in the PDF text.

    **<DATA>**
    """
            + text
            + """
    **</DATA>**

    Respond ONLY with CSV content. Do not summarize or explain.
    """
        )


def extract_csv_from_gpt(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a CSV table extractor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


def save_csv(output_file, csv_text):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(csv_text)
    print(f"✅ Saved CSV: {output_file}")


def process_all_pdfs():
    """Process all PDF files in the extracted data directories."""
    all_homes_results = []
    detached_results = []

    # Process ALL HOME TYPES PDFs
    all_homes_files = sorted(
        [f for f in os.listdir(ALL_HOMES_DIR) if f.lower().endswith(".pdf")]
    )

    all_homes_files = list(filter(lambda x: x >= "2020-01", all_homes_files))

    print(f"\nProcessing {len(all_homes_files)} ALL HOME TYPES PDFs...")
    for pdf_file in all_homes_files:
        date_str = pdf_file.split(".")[0]
        pdf_path = ALL_HOMES_DIR / pdf_file
        output_file = ALL_HOMES_CSV_DIR / f"{date_str}.csv"

        if output_file.exists():
            print(f"CSV already exists: {output_file}")
            continue

        print(f"Processing ALL HOME TYPES: {pdf_file} (Date: {date_str})...")
        process_pdf(pdf_path, output_file, "all_home_types")

        all_homes_results.append(
            {
                "filename": pdf_file,
                "date": date_str,
            }
        )

    # Process DETACHED PDFs
    detached_files = sorted(
        [f for f in os.listdir(DETACHED_DIR) if f.lower().endswith(".pdf")]
    )

    detached_files = list(filter(lambda x: x >= "2020-01", detached_files))

    print(f"\nProcessing {len(detached_files)} DETACHED PDFs...")
    for pdf_file in detached_files:
        date_str = pdf_file.split(".")[0]
        pdf_path = DETACHED_DIR / pdf_file
        output_file = DETACHED_CSV_DIR / f"{date_str}.csv"

        if output_file.exists():
            print(f"CSV already exists: {output_file}")
            continue

        print(f"Processing DETACHED: {pdf_file} (Date: {date_str})...")
        success, shape = process_pdf(pdf_path, output_file, "detached")

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

    print("\nStatistics:")
    print(
        f"ALL HOME TYPES: {successful_all_homes}/{total_all_homes} successful ({successful_all_homes / total_all_homes * 100:.1f}%)"
    )
    print(
        f"DETACHED: {successful_detached}/{total_detached} successful ({successful_detached / total_detached * 100:.1f}%)"
    )


def process_pdf(pdf_path, output_file, property_type="detached"):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    text = extract_page_text(pdf_path)
    prompt = generate_prompt(text, base_name)
    csv = extract_csv_from_gpt(prompt)
    save_csv(output_file, csv)


if __name__ == "__main__":
    process_all_pdfs()
