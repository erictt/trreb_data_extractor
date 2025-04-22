.PHONY: setup clean fetch extract fetch-extract convert normalize economy forecast lint format

# Default Python interpreter
PYTHON := python3

# Virtual environment
VENV := .venv
VENV_ACTIVATE := $(VENV)/bin/activate

# Default data directories
DATA_DIR := data
PDF_DIR := $(DATA_DIR)/pdfs
EXTRACTED_DIR := $(DATA_DIR)/extracted
PROCESSED_DIR := $(DATA_DIR)/processed
ECONOMIC_DIR := $(DATA_DIR)/economic
FORECAST_DIR := $(DATA_DIR)/forecasts

setup:  ## Set up Python virtual environment and install dependencies
	@echo "Setting up TRREB Data Extractor environment..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	else \
		echo "Virtual environment already exists. Updating it..."; \
	fi
	@. $(VENV_ACTIVATE) && pip install --upgrade pip
	@. $(VENV_ACTIVATE) && pip install -e .
	@echo "Setup complete!"

clean:  ## Remove generated files and directories
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"

fetch:  ## Download TRREB PDFs only
	@echo "Downloading TRREB PDFs..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli fetch --operation fetch --log-level DEBUG

extract:  ## Extract relevant pages from PDFs
	@echo "Extracting pages from PDFs..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli fetch --operation extract

fetch-extract:  ## Download and extract TRREB PDFs in one operation
	@echo "Downloading and extracting TRREB PDFs..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli fetch --operation both --log-level DEBUG

convert:  ## Convert extracted pages to CSV format
	@echo "Converting all home types data to CSV..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli convert --type all_home_types
	@echo "Converting detached homes data to CSV..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli convert --type detached

normalize:  ## Normalize and validate the converted CSV data
	@echo "Normalizing all home types data..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli normalize --type all_home_types --validate
	@echo "Normalizing detached homes data..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli normalize --type detached --validate

economy:  ## Download and process economic indicators data
	@echo "Processing economic indicators data..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli economy

forecast:  ## Run forecasting pipeline for median prices
	@echo "Running forecasts for all home types..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli forecast \
		--input-type all_home_types \
		--model-type all \
		--target-variable "Median Price" \
		--plot
	@echo "Running forecasts for detached homes..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli forecast \
		--input-type detached \
		--model-type all \
		--target-variable "Median Price" \
		--plot

lint:  ## Run linters (flake8, black, isort, mypy)
	@echo "Running linters..."
	@. $(VENV_ACTIVATE) && flake8 trreb/
	@. $(VENV_ACTIVATE) && black --check trreb/
	@. $(VENV_ACTIVATE) && isort --check-only trreb/
	@. $(VENV_ACTIVATE) && mypy trreb/

format:  ## Format code using black and isort
	@echo "Formatting code..."
	@. $(VENV_ACTIVATE) && black trreb/
	@. $(VENV_ACTIVATE) && isort trreb/

# Create data directories
$(PDF_DIR) $(EXTRACTED_DIR) $(PROCESSED_DIR) $(ECONOMIC_DIR) $(FORECAST_DIR):
	@mkdir -p $@

# Data directory dependencies
fetch: $(PDF_DIR)
extract: $(EXTRACTED_DIR)
fetch-extract: $(PDF_DIR) $(EXTRACTED_DIR)
convert: $(PROCESSED_DIR)
normalize: $(PROCESSED_DIR)
economy: $(ECONOMIC_DIR)
forecast: $(FORECAST_DIR)
