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

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Make scripts executable
chmod +x extract_tables_enhanced.py
chmod +x run_extraction.sh

echo ""
echo "Setup complete! Run './run_extraction.sh' to start the extraction process."
