"""
Table extractor for TRREB reports prior to January 2020.
"""

import re
from pathlib import Path
from typing import List, Optional

import pandas as pd
import tabula
import warnings

from trreb.config import COLUMN_NAME_MAPPING, REGION_NAME_MAPPING
from trreb.services.csv_converter.base import TableExtractor
from trreb.utils.logging import logger

# Suppress annoying pandas warnings
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class Pre2020TableExtractor(TableExtractor):
    """Extractor for TRREB reports before January 2020 using tabula-py."""
    
    def __init__(self, property_type: str):
        """
        Initialize the extractor.
        
        Args:
            property_type: Type of property data to extract (all_home_types or detached)
        """
        super().__init__(property_type)
    
    def extract_table(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extract table from PDF using tabula-py.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DataFrame containing the extracted table data
        """
        logger.info(f"Extracting table from {pdf_path} using tabula-py")
        return self._extract_tabula_tables(pdf_path)
    
    def clean_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the extracted table data.
        
        Args:
            df: DataFrame containing the raw extracted table data
            
        Returns:
            Cleaned and standardized DataFrame
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Try to identify the data table structure
        df = self._identify_municipalities(df)
        
        # Remove rows where all values are NaN
        df = df.dropna(how="all")
        
        # For rows, try to identify if the first row is actually column headers
        if df.shape[0] > 0:
            first_row = df.iloc[0].astype(str)
            if any(
                col.lower() in " ".join(first_row.values).lower()
                for col in ["sales", "average price", "new listings", "active"]
            ):
                # First row appears to be headers
                new_headers = df.iloc[0]
                df = df.iloc[1:]
                df.columns = new_headers
                
                # Reapply column name cleaning
                df.columns = [
                    str(col).strip().replace("\n", " ").replace("\r", "")
                    for col in df.columns
                ]
                df.columns = [re.sub(r"\s+", " ", col) for col in df.columns]
        
        # Remove any unwanted rows based on specific patterns
        unwanted_patterns = ["Source:", "Notes:", "Copyright", "© 20", "Market Watch"]
        for pattern in unwanted_patterns:
            if "Municipality" in df.columns:
                df = df[~df["Municipality"].astype(str).str.contains(pattern, na=False)]
            else:
                # If no Municipality column, check the first column
                first_col = df.columns[0]
                df = df[~df[first_col].astype(str).str.contains(pattern, na=False)]
        
        # Try to convert numeric columns
        numeric_cols = [
            "Sales",
            "Dollar Volume",
            "Average Price",
            "Median Price",
            "New Listings",
            "Active Listings",
            "Avg. DOM",
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                try:
                    # Remove $ and , characters for price columns
                    if any(x in col for x in ["Price", "Volume"]):
                        df[col] = df[col].astype(str).str.replace("$", "", regex=False)
                        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
                    
                    # Convert to numeric
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                except Exception as e:
                    logger.warning(f"Error converting {col} to numeric: {e}")
        
        # Handle percentage columns
        pct_cols = ["Avg. SP/LP", "SNLR (Trend)"]
        for col in pct_cols:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.replace("%", "", regex=False)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                except Exception as e:
                    logger.warning(f"Error converting {col} to numeric: {e}")
        
        # Replace NaN in the first column header with 'Municipality'
        if pd.isna(df.columns[0]) or df.columns[0] == "":
            df.columns = ["Municipality"] + list(df.columns[1:])
        
        # Remove empty trailing columns (columns where all values are NaN)
        df = df.dropna(axis=1, how="all")
        
        # Remove any rows that contain footnote markers
        if df.shape[1] > 0 and "Municipality" in df.columns:
            # Remove rows where Municipality is just a number
            df = df[~df["Municipality"].astype(str).str.match(r"^\d+$", na=False)]
            # Remove summary or footnote rows
            footnote_patterns = ["SUMMARY OF", "Copyright", "Source:", "Notes:", "© 20"]
            for pattern in footnote_patterns:
                df = df[
                    ~df["Municipality"]
                    .astype(str)
                    .str.contains(pattern, na=False, case=False)
                ]
        
        # Remove the last row with the first cell of number
        df = df[~df.iloc[:, 0].astype(str).str.match(r"^\d+$", na=False)]
        
        # Standardize column names
        df = self._standardize_column_names(df)
        
        # Standardize region names
        df = self._standardize_region_names(df)
        
        return df
    
    def _extract_tabula_tables(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extract tables using tabula with different strategies.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            The largest extracted table
        """
        tables = []
        
        try:
            # First try with lattice=True (for tables with lines/borders)
            tables = tabula.read_pdf(
                str(pdf_path), pages="1", multiple_tables=True, lattice=True
            )
            
            # If no tables or small tables found, try with stream=True
            if not tables or all(t.shape[0] < 5 for t in tables if not t.empty):
                tables = tabula.read_pdf(
                    str(pdf_path), pages="1", multiple_tables=True, lattice=False, stream=True
                )
            
            # Select the largest table
            if tables:
                largest_table = max(
                    tables, key=lambda t: t.shape[0] * t.shape[1] if not t.empty else 0
                )
                return largest_table
        except Exception as e:
            logger.error(f"Error extracting tables with tabula: {e}")
        
        return pd.DataFrame()
    
    def _identify_municipalities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify the column or row containing municipality names and transform if needed.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with municipalities properly structured
        """
        if df is None or df.empty:
            return df
        
        # Common municipalities to look for
        key_municipalities = [
            "TREB Total",
            "TRREB Total",
            "Halton Region",
            "Peel Region",
            "City of Toronto",
            "York Region",
            "Durham Region",
        ]
        
        # Check if municipalities are in the first column
        if df.shape[1] > 0:
            first_col = df.iloc[:, 0].astype(str)
            if any(muni in " ".join(first_col.values) for muni in key_municipalities):
                return df
        
        # If municipalities are not in the first column, check other columns
        for col in range(1, min(df.shape[1], 3)):  # Check first few columns
            col_values = df.iloc[:, col].astype(str)
            if any(muni in " ".join(col_values.values) for muni in key_municipalities):
                # Move this column to the first position
                cols = list(df.columns)
                cols.insert(0, cols.pop(col))
                return df[cols]
        
        # If municipalities are in rows rather than columns, transpose the DataFrame
        for row in range(min(df.shape[0], 5)):  # Check first few rows
            row_values = df.iloc[row, :].astype(str)
            if any(muni in " ".join(row_values.values) for muni in key_municipalities):
                # Use this row as the header
                new_header = df.iloc[row]
                df = df.iloc[row + 1:]
                df.columns = new_header
                return df
        
        return df  # Return original if we couldn't identify municipalities
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names using the mapping from config.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with standardized column names
        """
        if df.empty:
            return df
            
        # Create a new dictionary for columns that actually exist in the DataFrame
        column_mapping = {col: COLUMN_NAME_MAPPING.get(col, col) for col in df.columns}
        
        # Rename the columns
        df = df.rename(columns=column_mapping)
        
        return df
    
    def _standardize_region_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize region names using the mapping from config.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with standardized region names
        """
        if df.empty:
            return df
            
        # Identify the region column (usually the first column)
        region_col = df.columns[0]
        
        # Apply the mapping to the region column
        df[region_col] = df[region_col].apply(
            lambda x: REGION_NAME_MAPPING.get(x, x) if pd.notna(x) else x
        )
        
        return df
