# TRREB Data Extractor

A comprehensive package for extracting, processing, and analyzing Toronto Regional Real Estate Board (TRREB) market reports to support housing price prediction in the Greater Toronto Area (GTA).

## Overview

The TRREB Data Extractor is a Python package that streamlines the collection and preparation of real estate market data from the Toronto Regional Real Estate Board. It downloads and processes TRREB market reports to extract relevant real estate data into structured formats, then enriches this data with economic indicators to facilitate machine learning-based housing price prediction.

## Features

- **Automated Data Collection**: Downloads market reports from the TRREB website (2016-present)
- **Five-Stage Processing Pipeline**:
  1. **PDF Page Extraction**: Extracts specific pages from PDF reports
  2. **Table Conversion**: Converts PDF tables to CSV using methods based on report format:
     - Pre-2020 reports: Uses tabula-py for tabular data extraction
     - Post-2020 reports: Uses AI (Grok API) for more accurate extraction of complex tables
  3. **Data Normalization**: Cleans, normalizes, and validates the extracted data
  4. **Economic Data Integration**: Integrates with economic indicators
  5. **Time Series Forecasting**: Generates market predictions using multiple models
- **Comprehensive Data Processing**:
  - Extracts both "All Home Types" and "Detached" property data
  - Preserves regional hierarchy information
  - Normalizes column names and data formats across different years
  - Validates data quality and consistency
- **Economic Data Integration**:
  - Integrates key economic indicators (interest rates, employment, inflation, etc.)
  - Adds lagged indicators for time series analysis
  - Creates integrated datasets ready for modeling
- **Time Series Forecasting**:
  - Multiple forecasting models (SARIMAX, LightGBM)
  - Automated model selection and optimization
  - Performance evaluation and visualization
  - Support for different forecast horizons
- **Command-Line Interface**:
  - Unified command structure with clear separation of concerns
  - Configurable options for each stage of the pipeline
  - Support for skipping existing files to improve performance

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
│   ├── services/            # Core services
│   │   ├── fetcher/         # Downloads PDFs and extracts pages
│   │   ├── converter/       # Converts extracted PDF pages to CSV format
│   │   ├── normalizer/      # Data cleaning, normalization, and validation
│   │   ├── economic/        # Economic data integration
│   │   └── forecasting/     # Time series forecasting models
│   ├── cli/                 # Command-line interface
│   │   ├── commands/        # Individual command modules
│   │   │   ├── fetch.py     # Fetch command implementation (download/extract)
│   │   │   ├── convert.py   # Convert command implementation (PDF to CSV)
│   │   │   ├── normalize.py # Normalize command implementation
│   │   │   ├── economy.py   # Economy command implementation
│   │   │   └── forecast.py  # Forecast command implementation
│   │   └── __main__.py      # CLI entry point
│   └── utils/               # Utility functions
│
├── data/                    # Data directory
│   ├── pdfs/               # Downloaded PDFs
│   ├── extracted/          # Extracted pages
│   ├── processed/          # Processed CSVs
│   ├── economic/          # Economic indicator data
│   └── forecasts/         # Forecast outputs and models
│
├── docs/                   # Documentation
└── tests/                 # Tests (removed)
```

## Usage

### Command-Line Interface

The package provides a unified command-line interface through the `trreb.cli` module:

```bash
# Download reports only
python -m trreb.cli fetch --operation fetch

# Extract pages from PDFs
python -m trreb.cli fetch --operation extract

# Download and extract in one operation
python -m trreb.cli fetch --operation both

# Convert extracted PDF pages to CSV
python -m trreb.cli convert --type all_home_types

# Normalize and validate data
python -m trreb.cli normalize --type all_home_types --validate

# Download/process/integrate economic indicators
python -m trreb.cli economy

# Generate forecasts
python -m trreb.cli forecast --input-type all_home_types --target-variable "Median Price"
```

### Command Options

#### Fetch Command

```bash
# Download reports from a specific year
python -m trreb.cli fetch --operation fetch --start-year 2020

# Extract with overwrite option
python -m trreb.cli fetch --operation extract --overwrite

# Extract a specific PDF
python -m trreb.cli fetch --operation extract --pdf data/pdfs/mw2301.pdf

# Download and extract with detailed logging
python -m trreb.cli fetch --operation both --start-year 2020 --log-level DEBUG
```

#### Convert Command

```bash
# Convert all home types data
python -m trreb.cli convert --type all_home_types

# Convert detached property data with overwrite option
python -m trreb.cli convert --type detached --overwrite

# Convert data for a specific date
python -m trreb.cli convert --type all_home_types --date 2020-01
```

#### Normalize Command

```bash
# Normalize all home types data with validation
python -m trreb.cli normalize --type all_home_types --validate

# Normalize detached property data
python -m trreb.cli normalize --type detached

# Normalize data for a specific date
python -m trreb.cli normalize --type all_home_types --date 2020-01
```

#### Economy Command

```bash
# Basic usage
python -m trreb.cli economy

# With additional options
python -m trreb.cli economy --force-download --include-lags

# Integrate with specific property type
python -m trreb.cli economy --property-type all_home_types
```

#### Forecast Command

```bash
# Basic forecast for median prices
python -m trreb.cli forecast --input-type all_home_types --target-variable "Median Price"

# Advanced forecast with all models and plots
python -m trreb.cli forecast \
    --input-type detached \
    --model-type all \
    --target-variable "Median Price" \
    --forecast-horizon 12 \
    --region "City of Toronto" \
    --save-model \
    --plot

# Run forecasts for specific model type
python -m trreb.cli forecast \
    --input-type all_home_types \
    --model-type sarimax \
    --target-variable "Sales" \
    --region "TRREB Total"
```

The forecast command supports these options:
- `--input-type`: Type of housing data ("all_home_types" or "detached")
- `--model-type`: Model selection ("sarimax", "lgbm", or "all")
- `--target-variable`: Variable to forecast (e.g., "Median Price", "Sales")
- `--forecast-horizon`: Number of months ahead to forecast
- `--region`: Specific region to forecast
- `--output-dir`: Custom directory for forecast results
- `--save-model`: Save trained models for later use
- `--plot`: Generate forecast visualizations

### Forecast Directory Structure

The forecasting service creates organized output directories:
```
data/forecasts/
└── {input_type}_{target_variable}_{region}_{timestamp}/
    ├── prepared_data.csv            # Prepared training data
    ├── predictions_sarimax.csv      # SARIMAX model predictions
    ├── predictions_lgbm.csv         # LightGBM model predictions
    ├── plot_sarimax.png            # SARIMAX forecast plot
    ├── plot_lgbm.png               # LightGBM forecast plot
    ├── model_sarimax.joblib        # Saved SARIMAX model
    ├── model_lgbm.joblib           # Saved LightGBM model
    └── run_summary.json            # Run configuration and metrics
```

See [forecasting.md](docs/forecasting.md) for detailed documentation of the forecasting functionality.

### Makefile

The Makefile includes several useful targets:

- **`make setup`**: Sets up the Python virtual environment and installs dependencies
- **`make fetch`**: Only downloads the TRREB PDFs
- **`make extract`**: Only extracts the relevant pages
- **`make fetch-extract`**: Downloads and extracts TRREB PDFs in one operation
- **`make convert`**: Converts extracted PDF pages to CSV format
- **`make normalize`**: Normalizes and validates the converted CSV data
- **`make economy`**: Downloads/processes/integrates economic indicators
- **`make forecast`**: Runs the forecasting pipeline for all property types
- **`make clean`**: Cleans up generated files and directories
- **`make lint`**: Runs linting tools (flake8, black, isort, mypy)
- **`make format`**: Formats code using black and isort

#### Debugging

To enable debug logging, use the `--log-level` parameter with any command:

```bash
python -m trreb.cli fetch --operation fetch --log-level DEBUG
```

Or when using make:

```bash
# Some commands already include DEBUG level
make fetch

# For other commands, use environment variables
LOG_LEVEL=DEBUG make convert
```

Debug logs are helpful for troubleshooting issues with the data pipeline.

## Data Processing Pipeline

The package implements a comprehensive data processing pipeline:

1. **Download and Extract TRREB Data**: Download monthly market reports and extract relevant pages
2. **Convert PDFs to CSV**: Convert tables to structured data format
3. **Normalize Data**: Clean, standardize, and validate the data
4. **Integrate Economic Data**: Add relevant economic indicators
5. **Generate Forecasts**: Create and evaluate market predictions

The pipeline creates a clear separation of concerns and optimizes performance through smart file existence checks.

For more detailed documentation on specific components, see:
- [data_complexity.md](docs/data_complexity.md) - Data processing challenges and solutions
- [economic_indicators.md](docs/economic_indicators.md) - Available economic indicators
- [forecasting.md](docs/forecasting.md) - Time series forecasting documentation

## License

MIT

## Acknowledgements

- Toronto Regional Real Estate Board (TRREB) for providing the market data
- Bank of Canada, Statistics Canada, and CMHC for economic data
- Xai for providing the Grok AI API used in extraction
- Claude AI for vibe coding