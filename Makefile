.PHONY: setup clean download extract process enrich pipeline test lint format docs help

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

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

download:  ## Download TRREB PDFs
	@echo "Downloading TRREB PDFs..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli.commands download

extract:  ## Extract relevant pages from PDFs
	@echo "Extracting pages from PDFs..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli.commands extract-pages

process:  ## Process extracted pages into CSV format
	@echo "Processing all home types data..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli.commands process --type all_home_types --validate --normalize
	@echo "Processing detached homes data..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m trreb.cli.commands process --type detached --validate --normalize

enrich:  ## Enrich processed data with economic indicators
	@echo "Enriching data with economic indicators..."
	@. $(VENV_ACTIVATE) && $(PYTHON) -m scripts.run_pipeline --skip-download --skip-extract --skip-process

pipeline:  ## Run complete data pipeline
	@echo "Running full pipeline..."
	@. $(VENV_ACTIVATE) && $(PYTHON) scripts/run_pipeline.py

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

test:  ## Run tests
	@echo "Running tests..."
	@. $(VENV_ACTIVATE) && pytest -xvs tests/

docs:  ## Generate documentation
	@echo "Generating documentation..."
	@. $(VENV_ACTIVATE) && cd docs && make html

# Create data directories
$(PDF_DIR) $(EXTRACTED_DIR) $(PROCESSED_DIR) $(ECONOMIC_DIR):
	@mkdir -p $@

# Data directory dependencies
download: $(PDF_DIR)
extract: $(EXTRACTED_DIR)
process: $(PROCESSED_DIR)
enrich: $(ECONOMIC_DIR)
