# TRREB Data Extractor

A comprehensive toolkit for working with Toronto Regional Real Estate Board (TRREB) Market Watch reports. This project includes tools to download, process, and analyze TRREB PDF reports.

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Download TRREB PDFs](#download-trreb-pdfs)
4. [Extract TRREB Areas Pages](#extract-trreb-areas-pages)
5. [Convert PDFs to CSV](#convert-pdfs-to-csv)
6. [Example Workflows](#example-workflows)

## Overview

This toolkit provides three main utilities:

1. **PDF Downloader** (`download_trreb_pdfs.py`): Downloads TRREB Market Watch reports from the official website.
2. **Areas Extractor** (`trreb_areas_extract.py`): Extracts specific pages from each report and categorizes by property type.
3. **PDF to CSV Converter** (`trreb_pdf_to_csv.py`): Converts the extracted PDF reports to structured CSV files using the Gemini API.

## File Structure

```
trreb_data_extractor/
├── .venv/                # Virtual environment
├── pdfs/                 # Original downloaded PDFs from TRREB
├── split-pdfs/           # Extracted pages organized by year and property type
│   ├── 2016/
│   ├── 2017/
│   └── ...
├── csv-outputs/          # Generated CSV files
├── download_trreb_pdfs.py    # Script to download PDFs from TRREB
├── trreb_areas_extract.py    # Script to extract relevant pages from PDFs
├── trreb_pdf_to_csv.py       # Script to convert PDFs to CSV
├── convert_trreb_pdfs.sh     # Shell wrapper for PDF to CSV conversion
└── README.md                 # This documentation
```

## Download TRREB PDFs

The PDF downloader script automatically fetches TRREB Market Watch reports from the official website.

### Features

- Downloads reports for all months from 2016 to the current date
- Avoids re-downloading existing files
- Uses concurrent downloading for efficiency
- Names files in a consistent format (`mwYYMM.pdf`)

### Usage

```bash
python download_trreb_pdfs.py
```

### Output

The script saves downloaded files to the `pdfs/` directory with filenames like `mw2201.pdf` (for January 2022).

## Extract TRREB Areas Pages

The areas extractor script processes the downloaded PDFs and extracts only the relevant "SUMMARY OF EXISTING HOME TRANSACTIONS" pages for ALL TRREB AREAS.

### Features

- Extracts only TRREB Areas summary pages (excludes City of Toronto Municipal Breakdown pages)
- Categorizes by property type (DETACHED, SEMI-DETACHED, CONDO APT, etc.)
- Organizes output by year
- Standardizes property type names (e.g., renames "ROW" to "TOWNHOUSE")
- Uses numeric month format in filenames

### Usage

```bash
python trreb_areas_extract.py
```

For debugging (shows extracted text for pages):
```bash
python trreb_areas_extract.py --debug
```

### Output

The script saves extracted PDF pages to the `split-pdfs/` directory, organized by year:

```
split-pdfs/
├── 2016/
│   ├── ALL_HOME_TYPES_2016_01.pdf
│   ├── CONDO_APT_2016_01.pdf
│   └── ...
├── 2017/
└── ...
```

## Convert PDFs to CSV

The PDF to CSV converter uses the Google Gemini API to extract structured data from the PDF pages.

### Features

- Converts TRREB PDF reports to structured CSV format
- Extracts tabular data including region names, sales, prices, listings, etc.
- Supports filtering by year and property type
- Processes multiple years and property types in a single run
- Detailed logging to track conversion progress

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (You can get one from [Google AI Studio](https://makersuite.google.com/))

### Installation

```bash
source .venv/bin/activate  # Activate the virtual environment
pip install google-generativeai
```

### Usage

Using the Python script directly:

```bash
python trreb_pdf_to_csv.py --years "2022,2023,2024" --property_types "DETACHED,CONDO_APT" --api_key "your_api_key"
```

Using the shell wrapper:

```bash
./convert_trreb_pdfs.sh "your_api_key" --years "2022,2023" --property_types "ALL_HOME_TYPES"
```

### Parameters

- `--years`: Year(s) to process, comma-separated (e.g., "2016", "2022,2023,2024") or "all" for all years (default: "all")
- `--property_types`: Type(s) of property to process, comma-separated (default: "ALL")
  - Available types: ALL_HOME_TYPES, CONDO_APT, CONDO_TOWNHOUSE, DETACHED, SEMI-DETACHED, TOWNHOUSE
- `--api_key`: Google Gemini API key (required)
- `--output_dir`: Output directory for CSV files (default: "./csv-outputs")

### Output

The script creates CSV files in the specified output directory, organized by year:

```
csv-outputs/
├── 2016/
│   ├── ALL_HOME_TYPES_2016_01.csv
│   ├── CONDO_APT_2016_01.csv
│   └── ...
├── 2017/
└── ...
```

Each CSV file contains structured real estate data including region names, sales figures, average prices, median prices, listings information, days on market, and sales-to-list price ratios.

## Example Workflows

### Complete End-to-End Processing

To process all TRREB Market Watch reports from scratch:

```bash
# 1. Download all reports
python download_trreb_pdfs.py

# 2. Extract relevant pages
python trreb_areas_extract.py

# 3. Convert to CSV
export GEMINI_API_KEY="your_api_key"
./convert_trreb_pdfs.sh --years "all" --property_types "ALL_HOME_TYPES,DETACHED,CONDO_APT"
```

### Process Recent Data Only

To process only the most recent two years of data:

```bash
# Download recent reports (script will only download missing ones)
python download_trreb_pdfs.py

# Extract pages for those years
python trreb_areas_extract.py

# Convert only recent years to CSV
./convert_trreb_pdfs.sh "your_api_key" --years "2023,2024" --property_types "ALL"
```

### Process Specific Property Types

To focus on a specific market segment:

```bash
# Convert only condo data to CSV
./convert_trreb_pdfs.sh "your_api_key" --property_types "CONDO_APT,CONDO_TOWNHOUSE" --years "all"
```
