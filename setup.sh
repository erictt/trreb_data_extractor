#!/bin/bash

# TRREB Data Extractor Setup Script

echo "Setting up TRREB Data Extractor environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists. Updating it..."
fi

# Activate virtual environment
source .venv/bin/activate

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -sSf https://install.determinate.systems/uv | sh
fi

# Install the package in development mode
echo "Installing dependencies..."
uv pip install -e .

# Create required directories
echo "Creating data directories..."
mkdir -p data/pdfs
mkdir -p data/extracted/all_home_types
mkdir -p data/extracted/detached
mkdir -p data/processed/all_home_types
mkdir -p data/processed/detached
mkdir -p data/economic

# Install additional development dependencies
echo "Installing development dependencies..."
uv pip install pytest black flake8 isort mypy

echo ""
echo "Setup complete! Activate the virtual environment with:"
echo "    source .venv/bin/activate"
echo ""
echo "Then run the full pipeline with:"
echo "    python scripts/run_pipeline.py"
echo ""
echo "Or use individual commands:"
echo "    python -m trreb.cli.commands download"
echo "    python -m trreb.cli.commands extract-pages"
echo "    python -m trreb.cli.commands process --type all_home_types"
echo ""
echo "Alternatively, use make commands if you have make installed:"
echo "    make pipeline    # Run full pipeline"
echo "    make download    # Download PDFs only"
echo "    make extract     # Extract pages only"
echo "    make process     # Process CSVs only"
echo "    make enrich      # Enrich with economic data"
