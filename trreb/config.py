"""
Configuration settings for the TRREB Data Extractor.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
EXTRACTED_DIR = DATA_DIR / "extracted"
PROCESSED_DIR = DATA_DIR / "processed"
ECONOMIC_DIR = DATA_DIR / "economic"

# Extracted data directories
ALL_HOMES_EXTRACTED_DIR = EXTRACTED_DIR / "all_home_types"
DETACHED_EXTRACTED_DIR = EXTRACTED_DIR / "detached"

# Processed data directories
ALL_HOMES_PROCESSED_DIR = PROCESSED_DIR / "all_home_types"
DETACHED_PROCESSED_DIR = PROCESSED_DIR / "detached"

# Ensure all directories exist
for directory in [
    PDF_DIR, 
    ALL_HOMES_EXTRACTED_DIR, 
    DETACHED_EXTRACTED_DIR,
    ALL_HOMES_PROCESSED_DIR,
    DETACHED_PROCESSED_DIR,
    ECONOMIC_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# API Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-mini-fast-beta")

# Download configuration
TRREB_BASE_URL = "https://trreb.ca/wp-content/files/market-stats/market-watch/mw{}{:02d}.pdf"
START_YEAR = 2016
MAX_DOWNLOAD_WORKERS = 5

# Extraction configuration
EXTRACTION_CUTOFF_DATE = "2020-01"  # Date to switch extraction methods
SECOND_FORMAT_CUTOFF_DATE = "2022-04"  # Date to switch to the third format style

# Region name standardization mapping
REGION_NAME_MAPPING: Dict[str, str] = {
    "TREB Total": "TRREB Total",
    "TRREB Total": "TRREB Total",
    "All TRREB Areas": "TRREB Total",
    "E. Gwillimbury": "East Gwillimbury",
    "East Gwillimbury": "East Gwillimbury",
    "EGswsiallimbury": "East Gwillimbury",
    "GEswsiallimbury": "East Gwillimbury",
    "Whitchurch-Stouffville": "Whitchurch-Stouffville",
    "Stouffville": "Whitchurch-Stouffville",
    "Bradford West Gwillimbury": "Bradford West Gwillimbury",
    "Bradford West": "Bradford West Gwillimbury",
    "Bradford": "Bradford West Gwillimbury",
    "Adjala-Tosorontio": "Adjala-Tosorontio",
    "King Township": "King",
    "King": "King",
}

# Column name standardization mapping
COLUMN_NAME_MAPPING: Dict[str, str] = {
    "Number of Sales": "Sales",
    "# of Sales": "Sales",
    "Sales": "Sales",
    "Sales1": "Sales",
    "Dollar Volume1": "Dollar Volume",
    "Dollar Volume": "Dollar Volume",
    "Average Price1": "Average Price",
    "Average Price": "Average Price",
    "Median Price1": "Median Price",
    "Median Price": "Median Price",
    "New Listings2": "New Listings",
    "New Listings": "New Listings",
    "SNLR (Trend) 8": "SNLR Trend",
    "SNLR (Trend)8": "SNLR Trend",
    "SNLR (Trend)": "SNLR Trend",
    "SNLR Trend": "SNLR Trend",
    "Active Listings 3": "Active Listings",
    "Active Listings3": "Active Listings",
    "Active Listings": "Active Listings",
    "Mos. Inv. (Trend)9": "Months Inventory",
    "Mos. Inv. (Trend) 9": "Months Inventory",
    "Mos. Inv (Trend)": "Months Inventory",
    "Mos Inv (Trend)": "Months Inventory",
    "Mos. Inv. (Trend)": "Months Inventory",
    "Avg. SP / LP4": "Avg SP/LP",
    "Avg. SP/LP4": "Avg SP/LP",
    "Avg. SP/LP": "Avg SP/LP",
    "Avg SP/LP": "Avg SP/LP",
    "Avg. DOM5": "Avg DOM",
    "Avg. LDOM": "Avg DOM",
    "Avg DOM": "Avg DOM",
    "Avg. PDOM": "Avg PDOM",
    "Avg PDOM": "Avg PDOM",
}

# Expected column configurations for different property types and periods
# Pre-2020 (2016 to 2019-12)
PRE_2020_ALL_HOME_COLUMNS = [
    "Sales", "Dollar Volume", "Average Price", "Median Price", 
    "New Listings", "SNLR Trend", "Active Listings", "Months Inventory", 
    "Avg SP/LP", "Avg DOM"
]

PRE_2020_DETACHED_COLUMNS = [
    "Sales", "Dollar Volume", "Average Price", "Median Price", 
    "New Listings", "Active Listings", "Avg SP/LP", "Avg DOM"
]

# 2020-01 to 2022-04
MID_PERIOD_ALL_HOME_COLUMNS = [
    "Sales", "Dollar Volume", "Average Price", "Median Price", 
    "New Listings", "SNLR Trend", "Active Listings", "Months Inventory", 
    "Avg SP/LP", "Avg DOM", "Avg PDOM"
]

MID_PERIOD_DETACHED_COLUMNS = [
    "Sales", "Dollar Volume", "Average Price", "Median Price", 
    "New Listings", "Active Listings", "Avg SP/LP", "Avg DOM"
]

# Post 2022-04
POST_2022_ALL_HOME_COLUMNS = [
    "Sales", "Dollar Volume", "Average Price", "Median Price", 
    "New Listings", "SNLR Trend", "Active Listings", "Months Inventory", 
    "Avg SP/LP", "Avg DOM", "Avg PDOM"
]

POST_2022_DETACHED_COLUMNS = [
    "Sales", "Dollar Volume", "Average Price", "Median Price", 
    "New Listings", "Active Listings", "Avg SP/LP", "Avg DOM"
]

# List of all possible regions (for validation)
ALL_REGIONS: List[str] = [
    "TRREB Total",
    "Halton Region",
    "Burlington",
    "Halton Hills",
    "Milton",
    "Oakville",
    "Peel Region",
    "Brampton",
    "Caledon",
    "Mississauga",
    "City of Toronto",
    "Toronto West",
    "Toronto Central",
    "Toronto East",
    "York Region",
    "Aurora",
    "East Gwillimbury",
    "Georgina",
    "King",
    "Markham",
    "Newmarket",
    "Richmond Hill",
    "Vaughan",
    "Whitchurch-Stouffville",
    "Durham Region",
    "Ajax",
    "Brock",
    "Clarington",
    "Oshawa",
    "Pickering",
    "Scugog",
    "Uxbridge",
    "Whitby",
    "Dufferin County",
    "Orangeville",
    "Simcoe County",
    "Adjala-Tosorontio",
    "Bradford West Gwillimbury",
    "Essa",
    "Innisfil",
    "New Tecumseth",
]

# List of parent regions and their children for hierarchy maintenance
REGION_HIERARCHY: Dict[str, List[str]] = {
    "TRREB Total": [
        "Halton Region", "Peel Region", "City of Toronto", 
        "York Region", "Durham Region", "Dufferin County", "Simcoe County"
    ],
    "Halton Region": ["Burlington", "Halton Hills", "Milton", "Oakville"],
    "Peel Region": ["Brampton", "Caledon", "Mississauga"],
    "City of Toronto": ["Toronto West", "Toronto Central", "Toronto East"],
    "York Region": [
        "Aurora", "East Gwillimbury", "Georgina", "King", 
        "Markham", "Newmarket", "Richmond Hill", "Vaughan", "Whitchurch-Stouffville"
    ],
    "Durham Region": [
        "Ajax", "Brock", "Clarington", "Oshawa", 
        "Pickering", "Scugog", "Uxbridge", "Whitby"
    ],
    "Dufferin County": ["Orangeville"],
    "Simcoe County": [
        "Adjala-Tosorontio", "Bradford West Gwillimbury", 
        "Essa", "Innisfil", "New Tecumseth"
    ],
}
