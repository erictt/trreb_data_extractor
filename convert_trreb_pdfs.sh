#!/bin/bash
# A wrapper script for the TRREB PDF to CSV converter

# Exit on error
set -e

# Activate the virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"

# Check if API key is provided as environment variable or argument
if [ -n "$GEMINI_API_KEY" ]; then
    API_KEY="$GEMINI_API_KEY"
elif [ -n "$1" ]; then
    API_KEY="$1"
    shift
else
    echo "Error: Google Gemini API key is required"
    echo "Usage: $0 <api_key> [--years YEARS] [--property_types TYPES]"
    echo "   or: GEMINI_API_KEY=your_key $0 [--years YEARS] [--property_types TYPES]"
    echo ""
    echo "Examples:"
    echo "  $0 your_api_key --years 2022,2023,2024 --property_types DETACHED,CONDO_APT"
    echo "  GEMINI_API_KEY=your_key $0 --years all --property_types ALL_HOME"
    exit 1
fi

# Run the Python script with the provided arguments
python "$SCRIPT_DIR/trreb_pdf_to_csv.py" --api_key "$API_KEY" "$@"
