# TRREB Data Extractor

A tool for extracting, processing, and analyzing Toronto Regional Real Estate Board (TRREB) market reports.

## Overview

This project downloads and processes TRREB market reports (PDFs) to extract relevant real estate market data into a structured CSV format. It extracts data for both "All Home Types" and "Detached" property categories.

The tool handles different TRREB report formats across years (pre-2020 and post-2020) using different extraction methods:
- For reports prior to January 2020: Uses tabula-py to extract tabular data
- For reports from January 2020 onwards: Uses AI (Grok API) for more accurate extraction of complex table structures

## Features

- Download TRREB market reports from 2016 to present
- Extract specific pages for "All Home Types" and "Detached" property data
- Process extracted PDF pages into structured CSV format
- Support for different report formats over the years
- Data is extracted with region hierarchies preserved (e.g., TRREB Total, Halton Region, Burlington, etc.)

## Installation

### Prerequisites

- Python 3.8+
- Required Python packages (see `requirements.txt`)
- For reports from January 2020 onwards: xAI API key (for Grok models)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd trreb_data_extractor
```

2. Run the setup script to create a virtual environment and install dependencies:
```bash
./setup.sh
```

3. Create a `.env` file with your API key (for processing reports from January 2020 onwards):
```
XAI_API_KEY=your_xai_api_key_here
```

## Usage

The extraction process has three main steps:

### 1. Download TRREB PDFs

```bash
python download_trreb_pdfs.py
```

This will download all available TRREB market reports from 2016 to the present and store them in the `pdfs/` directory.

### 2. Extract Relevant Pages

```bash
python all_home_detached_extract.py
```

This extracts the "All Home Types" and "Detached" property pages from each PDF and saves them to:
- `extracted_data/all_home_types/`
- `extracted_data/detached/`

### 3. Process Pages into CSV format

For reports prior to January 2020:
```bash
python extract_prior_to_2020_01.py
```

For reports from January 2020 onwards:
```bash
python extract_after_2020_01.py
```

These scripts process the extracted PDF pages and generate CSV files in:
- `csv_data/all_home_types/`
- `csv_data/detached/`

## Data Structure

The extracted CSVs include the following data (columns may vary based on the time period):

### All Home Types (2020-01 and later)
- Region
- # of Sales/Sales
- Dollar Volume
- Average Price
- Median Price
- New Listings
- SNLR (Trend)
- Active Listings
- Mos Inv (Trend)
- Avg. SP/LP
- Avg. LDOM
- Avg. PDOM

### Detached (2020-01 and later)
- Region
- # of Sales/Sales
- Dollar Volume
- Average Price
- Median Price
- New Listings
- Active Listings
- Avg. SP/LP
- Avg. LDOM

## Notes

- The extraction process uses different methods based on the report date to handle format changes over time
- The AI extraction method (using Grok) is more accurate for complex table structures in newer reports
- Data is extracted with region hierarchies preserved for easier analysis
- Both date-based file naming and source-file tracking are supported for reliable data provenance

## Directory Structure

```
trreb_data_extractor/
├── download_trreb_pdfs.py      # Downloads PDFs from TRREB website
├── all_home_detached_extract.py # Extracts specific pages from PDFs
├── extract_prior_to_2020_01.py  # Processes older reports
├── extract_after_2020_01.py     # Processes newer reports using AI
├── setup.sh                    # Setup script
├── requirements.txt            # Python dependencies
├── .env                        # API key configuration (create this)
├── pdfs/                       # Downloaded PDFs
├── extracted_data/             # Extracted PDF pages
│   ├── all_home_types/
│   └── detached/
└── csv_data/                   # Processed CSV files
    ├── all_home_types/
    └── detached/
```
