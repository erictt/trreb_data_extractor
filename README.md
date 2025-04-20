# TRREB Data Extractor

A comprehensive package for extracting, processing, and analyzing Toronto Regional Real Estate Board (TRREB) market reports to support housing price prediction in the Greater Toronto Area (GTA).

## Overview

The TRREB Data Extractor is a Python package that streamlines the collection and preparation of real estate market data from the Toronto Regional Real Estate Board. It downloads and processes TRREB market reports to extract relevant real estate data into structured formats, then enriches this data with economic indicators to facilitate machine learning-based housing price prediction.

## Features

- **Automated Data Collection**: Downloads market reports from the TRREB website (2016-present)
- **Intelligent Extraction**: Processes PDFs using appropriate methods based on report format:
  - Pre-2020 reports: Uses tabula-py for tabular data extraction
  - Post-2020 reports: Uses AI (Grok API) for more accurate extraction of complex tables
- **Comprehensive Data Processing**:
  - Extracts both "All Home Types" and "Detached" property data
  - Preserves regional hierarchy information
  - Normalizes column names and data formats across different years
  - Validates data quality and consistency
- **Economic Data Integration**:
  - Integrates key economic indicators (interest rates, employment, inflation, etc.)
  - Adds lagged indicators for time series analysis
  - Creates enriched datasets ready for modeling
- **Command-Line Interface**:
  - Run complete data pipeline with a single command
  - Execute specific steps as needed (download, extract, process, enrich)
  - Configure validation and normalization options

## Installation

### Prerequisites

- Python 3.11+
- Required Python packages (see `pyproject.toml`)
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
   
   The setup script uses `uv` for faster dependency installation. If you don't have `uv` installed, you can install it with:
   ```bash
   curl -sSf https://install.determinate.systems/uv | sh
   ```

3. Create a `.env` file with your API key (for processing reports from January 2020 onwards):
   ```
   XAI_API_KEY=your_xai_api_key_here
   ```

## Package Structure

```
trreb_data_extractor/
├── trreb/                    # Main package directory
│   ├── downloader/           # PDF downloading module
│   ├── extractor/            # PDF extraction module
│   ├── processor/            # Data processing module
│   ├── economic/             # Economic data integration
│   ├── ml/                   # Machine learning module (placeholder)
│   ├── cli/                  # Command-line interface
│   └── utils/                # Utility functions
│
├── data/                     # Data directory
│   ├── pdfs/                 # Downloaded PDFs
│   ├── extracted/            # Extracted pages
│   ├── processed/            # Processed CSVs
│   └── economic/             # Economic indicator data
│
├── docs/                     # Documentation
├── scripts/                  # Standalone scripts
└── tests/                    # Tests (future)
```

## Usage

### Command-Line Interface

Run the complete pipeline:

```bash
python scripts/run_pipeline.py
```

Or run specific steps:

```bash
# Download reports
python -m trreb.cli.commands download

# Extract pages
python -m trreb.cli.commands extract-pages

# Process extracted pages
python -m trreb.cli.commands process --type all_home_types --validate --normalize

# Run pipeline with options
python scripts/run_pipeline.py --skip-download --validate --normalize
```


#### Makefile

The Makefile includes several useful targets:

- **`make setup`**: Sets up the Python virtual environment and installs dependencies
- **`make pipeline`**: Runs the full data pipeline (download, extract, process, enrich)
- **`make download`**: Only downloads the TRREB PDFs
- **`make extract`**: Only extracts the relevant pages
- **`make process`**: Only processes the extracted pages into CSVs
- **`make enrich`**: Only enriches with economic indicators
- **`make clean`**: Cleans up generated files and directories
- **`make lint`**: Runs linting tools (flake8, black, isort, mypy)
- **`make format`**: Formats code using black and isort
- **`make test`**: Runs tests
- **`make docs`**: Generates documentation
- **`make help`**: Shows available commands with descriptions

## Data Processing Pipeline

1. **Download TRREB PDFs**: Download monthly market reports from the TRREB website.
2. **Extract Relevant Pages**: Identify and extract pages containing "All Home Types" and "Detached" property data.
3. **Process PDFs into CSV**: Convert PDF tables to structured CSV data using appropriate extraction method based on report date.
4. **Normalize Data**: Standardize column names, region names, and data formats.
5. **Validate Data**: Check for data quality issues, inconsistencies, and anomalies.
6. **Integrate Economic Data**: Enrich real estate data with economic indicators.
7. **Prepare for ML**: Create features and datasets ready for machine learning models.

## Economic Indicators

The package integrates several economic indicators relevant to housing prices:

- Interest Rates (Bank of Canada)
- Employment Metrics (Statistics Canada)
- Inflation and Consumer Price Indices
- Population and Migration
- Construction and Housing Supply (CMHC)

See [economic_indicators.md](docs/economic_indicators.md) for a detailed list of indicators and their sources.

## Data Complexity

The TRREB data presents several challenges:

- Format changes over time (different column names, region names, etc.)
- Inconsistent PDF layouts requiring different extraction methods
- Complex regional hierarchies
- Various numeric formats and units

See [data_complexity.md](docs/data_complexity.md) for a detailed explanation of these challenges and how they are addressed.

## Documentation

- [data_complexity.md](docs/data_complexity.md) - Details on TRREB data structure and challenges
- [economic_indicators.md](docs/economic_indicators.md) - Information on economic indicators and their integration
- [refactoring.md](docs/refactoring.md) - Documentation of the code restructuring process
- [general_prompt.md](docs/general_prompt.md) - General prompt template for AI-assisted development

## Future Development

Planned enhancements include:

1. **Machine Learning Module**: Implementation of feature engineering, model training, and evaluation for housing price prediction
2. **Additional Economic Indicators**: Integration of more detailed economic and demographic data
3. **Geographic Analysis**: Incorporation of location-based features
4. **Interactive Visualization**: Dashboard for exploring trends and predictions
5. **Automated Reporting**: Generation of regular market analysis reports

## License

MIT

## Acknowledgements

- Toronto Regional Real Estate Board (TRREB) for providing the market data
- Bank of Canada, Statistics Canada, and CMHC for economic data
- Xai for providing the Grok AI API used in extraction
- Claude AI for vibe coding
