# TRREB Data Extractor

A comprehensive tool for extracting, processing, and analyzing Toronto Regional Real Estate Board (TRREB) market reports for housing price prediction.

## Project Goal

This project aims to build a machine learning pipeline that accurately predicts housing prices in the Greater Toronto Area (GTA) and Ontario regions. The pipeline includes:

1. **Data Collection**: Automated downloading of TRREB market reports
2. **Data Extraction**: Converting PDF reports to structured data
3. **Data Enrichment**: Integrating economic indicators and other relevant factors
4. **Model Training**: Developing accurate predictive models for housing prices
5. **Analysis**: Providing insights into market trends and price drivers

## Overview

The TRREB Data Extractor downloads and processes TRREB market reports (PDFs) to extract relevant real estate market data into a structured CSV format. It handles different report formats across years (pre-2020 and post-2020) using specialized extraction methods. The extracted data includes metrics for both "All Home Types" and "Detached" property categories.

The data is intended to train machine learning models that can predict housing prices across different regions, accounting for historical trends, seasonal patterns, and economic factors.

## Features

- Download TRREB market reports from 2016 to present
- Extract specific pages for "All Home Types" and "Detached" property data
- Process extracted PDF pages into structured CSV format
- Support for different report formats over the years:
  - For reports prior to January 2020: Uses tabula-py to extract tabular data
  - For reports from January 2020 onwards: Uses AI (Grok API) for more accurate extraction of complex table structures
- Preserve region hierarchies (e.g., TRREB Total, Halton Region, Burlington, etc.)
- Data standardization to handle changing column names and formats over time

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

The extracted CSVs include detailed real estate market metrics by region, including:

- Sales counts
- Dollar volume
- Average and median prices
- New and active listings
- Sales-to-New-Listings Ratio (SNLR)
- Days on Market metrics
- And more market indicators

## Machine Learning Integration

The CSV data is designed to be used for training machine learning models to:

1. Predict housing prices across different regions and property types
2. Identify market trends and seasonal patterns
3. Determine key factors influencing price changes
4. Create forecasting models for specific districts

See the `docs/` directory for detailed information on:
- Data complexity and preprocessing considerations
- Economic indicators that can enhance prediction models
- Suggested machine learning approaches

## Project Structure

```
trreb_data_extractor/
├── download_trreb_pdfs.py      # Downloads PDFs from TRREB website
├── all_home_detached_extract.py # Extracts specific pages from PDFs
├── extract_prior_to_2020_01.py  # Processes older reports
├── extract_after_2020_01.py     # Processes newer reports using AI
├── setup.sh                    # Setup script
├── requirements.txt            # Python dependencies
├── .env                        # API key configuration (create this)
├── docs/                       # Project documentation
├── pdfs/                       # Downloaded PDFs
├── extracted_data/             # Extracted PDF pages
│   ├── all_home_types/
│   └── detached/
└── csv_data/                   # Processed CSV files
    ├── all_home_types/
    └── detached/
```

## Future Development

Planned enhancements include:
1. Integration of economic indicators (interest rates, unemployment, etc.)
2. Advanced data preprocessing pipeline
3. Feature engineering for ML model training
4. Model development and evaluation
5. Interactive visualization of predictions
6. Expanded property type coverage

## Notes

- The extraction process uses different methods based on the report date to handle format changes over time
- The AI extraction method (using Grok) is more accurate for complex table structures in newer reports
- Data is extracted with region hierarchies preserved for easier analysis
- Both date-based file naming and source-file tracking are supported for reliable data provenance

## Documentation

See the `docs/` directory for detailed documentation including:
- Data complexity overview
- Guide to economic indicators
- Development guidelines and prompts

## License

[Insert license information here]

## Acknowledgements

- Toronto Regional Real Estate Board (TRREB) for providing the market data
- [List any other acknowledgements]
