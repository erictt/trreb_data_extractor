"""
Extractor for TRREB reports from January 2020 onwards using AI models.
"""

import os
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import pdftotext
from openai import OpenAI

from trreb.config import COLUMN_NAME_MAPPING, GROK_MODEL, REGION_NAME_MAPPING, XAI_API_BASE_URL, XAI_API_KEY
from trreb.extractor.base import BaseExtractor
from trreb.utils.logging import logger


class Post2020Extractor(BaseExtractor):
    """Extractor for TRREB reports from January 2020 onwards using AI models."""
    
    def __init__(self, property_type: str):
        """
        Initialize the extractor.
        
        Args:
            property_type: Type of property data to extract (all_home_types or detached)
        """
        super().__init__(property_type)
        
        # Initialize OpenAI client if API key is available
        if XAI_API_KEY:
            self.client = OpenAI(
                api_key=XAI_API_KEY,
                base_url=XAI_API_BASE_URL,
            )
        else:
            logger.error("XAI_API_KEY not found. Cannot initialize AI extractor.")
            self.client = None
    
    def extract_table(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extract table from PDF using AI model.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DataFrame containing the extracted table data
        """
        if not self.client:
            logger.error("AI client not initialized. Cannot extract table.")
            return pd.DataFrame()
        
        logger.info(f"Extracting table from {pdf_path} using AI model")
        
        # Extract text from PDF
        page_text = self._extract_page_text(pdf_path)
        if not page_text:
            logger.error(f"Failed to extract text from {pdf_path}")
            return pd.DataFrame()
        
        # Generate prompt for AI model
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        prompt = self._generate_prompt(page_text, base_name)
        
        # Extract CSV from AI model
        csv_text = self._extract_csv_from_ai(prompt)
        if not csv_text:
            logger.error(f"Failed to extract CSV from AI model for {pdf_path}")
            return pd.DataFrame()
        
        # Convert CSV text to DataFrame
        try:
            df = pd.read_csv(pd.StringIO(csv_text))
            return df
        except Exception as e:
            logger.error(f"Error converting CSV text to DataFrame: {e}")
            return pd.DataFrame()
    
    def clean_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the extracted table data.
        
        Args:
            df: DataFrame containing the raw extracted table data
            
        Returns:
            Cleaned and standardized DataFrame
        """
        if df.empty:
            return df
        
        # The AI-extracted data is generally cleaner, but still needs standardization
        
        # Standardize column names
        df = self._standardize_column_names(df)
        
        # Standardize region names
        df = self._standardize_region_names(df)
        
        return df
    
    def _extract_page_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF page.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the first page
        """
        try:
            with open(pdf_path, "rb") as f:
                doc = pdftotext.PDF(f)
            return doc[0]
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def _generate_prompt(self, text: str, source_name: str) -> str:
        """
        Generate a prompt for the AI model based on the PDF text.
        
        Args:
            text: Extracted text from the PDF
            source_name: Name of the source file (used to determine format)
            
        Returns:
            Prompt for the AI model
        """
        # Different prompts for different date ranges and property types
        if "2020-01" <= source_name <= "2022-04":
            if self.property_type == "all_home_types":
                return (
                    """
                Construct a CSV file containing real estate transaction data for a specified month, using the provided PDF text in the <DATA> section below. The PDF text is structured similarly to the Toronto Regional Real Estate Board's January 2020 report. The CSV must include the following columns: Region, # of Sales, Dollar Volume, Average Price, Median Price, New Listings, SNLR (Trend), Active Listings, Mos Inv (Trend), Avg. SP/LP, Avg. LDOM, Avg. PDOM. Adhere to the following formatting rules:

                1. The Region column should have no title in the CSV header (i.e., the first column header is empty).
                2. Extract data directly from the <DATA> section to populate the table, ensuring accuracy and completeness for the specified month indicated in the PDF text.
                3. Numeric values (e.g., # of Sales, New Listings, Active Listings) should be formatted without quotes unless they contain commas, in which case use double quotes.
                4. Monetary values (e.g., Dollar Volume, Average Price, Median Price) should include a dollar sign and commas for thousands (e.g., "$1,234,567") and be wrapped in quotes if commas are present.
                5. Percentage values (e.g., SNLR (Trend), Avg. SP/LP) should include a percent sign (e.g., "58.5%").
                6. Decimal values (e.g., Mos Inv (Trend)) should be formatted to one decimal place (e.g., "2.0").
                7. Wrap any field containing commas in double quotes to ensure proper CSV formatting.
                8. Preserve the hierarchical structure of regions (e.g., TREB Total, Halton Region, Burlington, etc.) as presented in the PDF text.

                **<DATA>**
                """
                    + text
                    + """
                **</DATA>**

                Respond ONLY with CSV content. Do not summarize or explain.
                """
                )
            else:  # detached
                return (
                    """
                Construct a CSV file containing real estate transaction data for a specified month, using the provided PDF text in the <DATA> section below. The PDF text is structured similarly to the Toronto Regional Real Estate Board's January 2020 report. The CSV must include the following columns: Region, # of Sales, Dollar Volume, Average Price, Median Price, New Listings, Active Listings, Avg. SP/LP, Avg. LDOM. Adhere to the following formatting rules:

                1. The Region column should have no title in the CSV header (i.e., the first column header is empty).
                2. Extract data directly from the <DATA> section to populate the table, ensuring accuracy and completeness for the specified month indicated in the PDF text.
                3. Numeric values (e.g., # of Sales, New Listings, Active Listings) should be formatted without quotes unless they contain commas, in which case use double quotes.
                4. Monetary values (e.g., Dollar Volume, Average Price, Median Price) should include a dollar sign and commas for thousands (e.g., "$1,234,567") and be wrapped in quotes if commas are present.
                5. Wrap any field containing commas in double quotes to ensure proper CSV formatting.
                6. Preserve the hierarchical structure of regions (e.g., TREB Total, Halton Region, Burlington, etc.) as presented in the PDF text.

                **<DATA>**
                """
                    + text
                    + """
                **</DATA>**

                Respond ONLY with CSV content. Do not summarize or explain.
                """
                )
        else:  # after 2022-04
            if self.property_type == "all_home_types":
                return (
                    """
                Construct a CSV file containing real estate transaction data for a specified month, using the provided PDF text in the `<DATA>` section below. The PDF text is structured similarly to the Toronto Regional Real Estate Board's June 2024 report. The CSV must include the following columns: Region, Sales, Dollar Volume, Average Price, Median Price, New Listings, SNLR Trend, Active Listings, Mos Inv (Trend), Avg. SP/LP, Avg. LDOM, Avg. PDOM. Adhere to the following formatting rules:

                1. The Region column should have no title in the CSV header (i.e., the first column header is empty).
                2. Extract data directly from the `<DATA>` section to populate the table, ensuring accuracy and completeness for the specified month indicated in the PDF text.
                3. Numeric values (e.g., Sales, New Listings, Active Listings) should be formatted without quotes unless they contain commas, in which case use double quotes.
                4. Monetary values (e.g., Dollar Volume, Average Price, Median Price) should include a dollar sign and commas for thousands (e.g., "$1,234,567") and be wrapped in quotes if commas are present.
                5. Percentage values (e.g., SNLR Trend, Avg. SP/LP) should include a percent sign (e.g., "40.3%").
                6. Decimal values (e.g., Mos Inv (Trend)) should be formatted to one decimal place (e.g., "3.0").
                7. Wrap any field containing commas in double quotes to ensure proper CSV formatting.
                8. Preserve the hierarchical structure of regions (e.g., All TRREB Areas, Halton Region, Burlington, etc.) as presented in the PDF text.

                **<DATA>**
                """
                    + text
                    + """
                **</DATA>**

                Respond ONLY with CSV content. Do not summarize or explain.
                """
                )
            else:  # detached
                return (
                    """
                Construct a CSV file containing real estate transaction data for a specified month, using the provided PDF text in the <DATA> section below. The PDF text is structured similarly to the Toronto Regional Real Estate Board's January 2020 report. The CSV must include the following columns: Region, # of Sales, Dollar Volume, Average Price, Median Price, New Listings, Active Listings, Avg. SP/LP, Avg. LDOM. Adhere to the following formatting rules:

                1. The Region column should have no title in the CSV header (i.e., the first column header is empty).
                2. Extract data directly from the `<DATA>` section to populate the table, ensuring accuracy and completeness for the specified month indicated in the PDF text.
                3. Numeric values (e.g., Sales, New Listings, Active Listings) should be formatted without quotes unless they contain commas, in which case use double quotes.
                4. Monetary values (e.g., Dollar Volume, Average Price, Median Price) should include a dollar sign and commas for thousands (e.g., "$1,234,567") and be wrapped in quotes if commas are present.
                5. Wrap any field containing commas in double quotes to ensure proper CSV formatting.
                6. Preserve the hierarchical structure of regions (e.g., All TRREB Areas, Halton Region, Burlington, etc.) as presented in the PDF text.

                **<DATA>**
                """
                    + text
                    + """
                **</DATA>**

                Respond ONLY with CSV content. Do not summarize or explain.
                """
                )
    
    def _extract_csv_from_ai(self, prompt: str) -> str:
        """
        Extract CSV data from AI model.
        
        Args:
            prompt: Prompt for the AI model
            
        Returns:
            CSV text extracted by the AI model
        """
        try:
            response = self.client.chat.completions.create(
                model=GROK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a CSV table extractor."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error extracting CSV from AI model: {e}")
            return ""
    
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
