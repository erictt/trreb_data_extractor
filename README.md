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

The package provides a unified command-line interface through the `trreb.cli` module. You can run the commands as follows:

```bash
# Complete pipeline
python -m trreb.cli pipeline

# Download reports
python -m trreb.cli download

# Extract pages
python -m trreb.cli extract

# Process extracted pages
python -m trreb.cli process --type all_home_types --validate --normalize

# Enrich data with economic indicators
python -m trreb.cli enrich
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

#### Debugging

To enable debug logging, use the `--log-level` parameter with any command:

```bash
python -m trreb.cli download --log-level DEBUG
```

Or when using make:

```bash
# The download command already includes DEBUG level
make download

# For other commands, use environment variables
LOG_LEVEL=DEBUG make extract
```

Debug logs are helpful for troubleshooting issues with the data pipeline.

## Data Processing Pipeline

1. **Download TRREB PDFs**: Download monthly market reports from the TRREB website.
2. **Extract Relevant Pages**: Identify and extract pages containing "All Home Types" and "Detached" property data.
3. **Process PDFs into CSV**: Convert PDF tables to structured CSV data using appropriate extraction method based on report date.
4. **Normalize Data**: Standardize column names, region names, and data formats.
5. **Validate Data**: Check for data quality issues, inconsistencies, and anomalies.
6. **Integrate Economic Data**: Enrich real estate data with economic indicators.
7. **Prepare for ML**: Create features and datasets ready for machine learning models.

## Economic Module

The package includes an economic module that downloads and processes economic indicators relevant to housing prices. This module retrieves data from various sources and prepares it for later integration with the TRREB real estate data during the machine learning training phase.

### Economic Data Sources

The economic module currently supports the following data sources:

1. **Bank of Canada Interest Rates**
   - Overnight Rate - The primary interest rate set by the central bank
   - Prime Rate - The base rate banks use to set interest rates for loans
   - 5-Year Fixed Mortgage Rate - The most common mortgage term in Canada

2. **Statistics Canada Economic Indicators**
   - Unemployment Rate (Ontario and Toronto)
   - Consumer Price Index (CPI) for all items and housing
   - New Housing Price Index
   - Population Estimates (Ontario and Toronto)

3. **CMHC Housing Data**
   - Housing Starts in GTA - New residential construction projects
   - Housing Completions in GTA - Finished housing units
   - Under Construction in GTA - Current building activity

### Using the Economic Module

#### Downloading Economic Data

Economic data can be downloaded and processed independently from the TRREB data. You can run this step using:

```bash
# Using the CLI (basic usage)
python -m trreb.cli economy

# Using the CLI with additional options
python -m trreb.cli economy --force-download --include-lags

# Using make
make economy
```

Available CLI options for the `economy` command:
- `--property-type [all_home_types|detached]`: Specify which property type dataset to integrate with (if available)
- `--include-lags`: Include lagged economic indicators (default: true)
- `--force-download`: Force re-download of economic data even if cached data exists
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Set logging level (default: INFO)

The economic data is downloaded from the respective sources and cached in CSV files in the `data/economic` directory:
- `bank_of_canada_rates.csv`: Interest rates data from Bank of Canada
- `statistics_canada_economic.csv`: Economic indicators from Statistics Canada
- `cmhc_housing_data.csv`: Housing supply metrics from CMHC
- `master_economic_data.csv`: Combined dataset of all economic indicators

The cached data is used in subsequent runs unless you specify `--force-download`.

**Note**: The economic module will download and prepare the economic data regardless of whether you have processed any TRREB data. If TRREB data is available, it will also create integrated datasets; if not, it will simply prepare the economic data for later use.

To complete the data pipeline after downloading economic data, you should process the TRREB data using:
```bash
# Process and normalize all home types data
python -m trreb.cli process --type all_home_types --normalize

# Process and normalize detached homes data
python -m trreb.cli process --type detached --normalize
```

This will create the normalized TRREB data files that can be integrated with the economic data.

#### How the Economic Data is Organized

1. **Raw Data Storage**: Individual CSV files for each data source in the `data/economic` directory.

2. **Master Dataset**: A combined dataset of all economic indicators in `master_economic_data.csv`.

3. **Enriched Real Estate Data**: The TRREB data enriched with economic indicators in:
   - `enriched_all_home_types.csv`: For all home types
   - `enriched_detached.csv`: For detached homes

4. **Date Alignment**: All economic data is aligned with the TRREB data using a `date_str` column in the format 'YYYY-MM'.

5. **Lagged Indicators**: The economic module creates lagged versions of economic indicators (1, 3, 6, and 12 months) to capture time-delayed effects of economic changes on housing prices.

#### Adding Additional Economic Indicators

To add a new economic data source:

1. Create a new class that inherits from `EconomicDataSource` in `trreb/economic/sources.py`
2. Implement the `download()` and `preprocess()` methods
3. Add your new data source to the `get_all_data_sources()` function

For more details on available economic indicators and their sources, see [economic_indicators.md](docs/economic_indicators.md).

## Data Complexity

The TRREB data presents several challenges:

- Format changes over time (different column names, region names, etc.)
- Inconsistent PDF layouts requiring different extraction methods
- Complex regional hierarchies
- Various numeric formats and units

See [data_complexity.md](docs/data_complexity.md) for a detailed explanation of these challenges and how they are addressed.

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
