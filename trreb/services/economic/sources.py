"""
Economic data sources for housing price prediction.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

from trreb.config import ECONOMIC_DIR
from trreb.utils.logging import logger


class EconomicDataSource(ABC):
    """Abstract base class for economic data sources."""
    
    def __init__(self, name: str, cache_dir: Path = ECONOMIC_DIR):
        """
        Initialize an economic data source.
        
        Args:
            name: Name of the data source
            cache_dir: Directory to cache downloaded data
        """
        self.name = name
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache file path
        self.cache_file = self.cache_dir / f"{self.name.lower().replace(' ', '_')}.csv"
    
    @abstractmethod
    def download(self) -> pd.DataFrame:
        """
        Download data from the source.
        
        Returns:
            DataFrame containing the downloaded data
        """
        pass
    
    @abstractmethod
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the downloaded data.
        
        Args:
            df: DataFrame containing the raw downloaded data
            
        Returns:
            Preprocessed DataFrame
        """
        pass
    
    def get_data(self, force_download: bool = False) -> pd.DataFrame:
        """
        Get data from the source, using cached data if available.
        
        Args:
            force_download: Whether to force download even if cached data is available
            
        Returns:
            DataFrame containing the data
        """
        # Use cached data if available and not forcing download
        if self.cache_file.exists() and not force_download:
            logger.info(f"Using cached data for {self.name}")
            try:
                df = pd.read_csv(self.cache_file)
                
                # Verify essential columns exist
                required_cols = ["year", "month", "date_str"]
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    logger.warning(f"Cached data for {self.name} is missing columns: {missing_cols}")
                    raise ValueError(f"Cached data format invalid, missing: {missing_cols}")
                
                logger.info(f"Loaded {len(df)} rows for {self.name} from cache")
                return df
            except Exception as e:
                logger.error(f"Error reading cached data for {self.name}: {e}")
                logger.info(f"Falling back to downloading for {self.name}")
                # Fall back to downloading
        
        # Download and preprocess data
        logger.info(f"Downloading data for {self.name}")
        df = self.download()
        
        if df is not None and not df.empty:
            df = self.preprocess(df)
            
            # Verify essential columns exist before caching
            required_cols = ["year", "month", "date_str"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Processed data for {self.name} is missing required columns: {missing_cols}")
                # Try to fix if possible
                if "date_str" in df.columns and "year" not in df.columns:
                    df["year"] = df["date_str"].str.split("-").str[0].astype("Int64")
                if "date_str" in df.columns and "month" not in df.columns:
                    df["month"] = df["date_str"].str.split("-").str[1].astype("Int64")
            
            # Cache data
            try:
                df.to_csv(self.cache_file, index=False)
                logger.info(f"Cached {len(df)} rows of data for {self.name} to {self.cache_file}")
            except Exception as e:
                logger.error(f"Error caching data for {self.name}: {e}")
        else:
            logger.warning(f"No data available from {self.name} source")
            # Return an empty DataFrame with the required columns
            df = pd.DataFrame(columns=["year", "month", "date_str"])
        
        return df


class BankOfCanadaRates(EconomicDataSource):
    """Bank of Canada interest rates data source."""
    
    def __init__(self):
        """Initialize the Bank of Canada interest rates data source."""
        super().__init__("Bank of Canada Rates")
        
        # API URLs
        self.overnight_rate_url = "https://www.bankofcanada.ca/valet/observations/V39079/json"
        self.prime_rate_url = "https://www.bankofcanada.ca/valet/observations/V80691311/json"
        self.mortgage_5yr_url = "https://www.bankofcanada.ca/valet/observations/V122521/json"
    
    def download(self) -> pd.DataFrame:
        """
        Download interest rates data from the Bank of Canada.
        
        Returns:
            DataFrame containing the interest rates data
        """
        try:
            # Download overnight rate
            overnight_resp = requests.get(self.overnight_rate_url)
            overnight_data = overnight_resp.json()
            
            # Download prime rate
            prime_resp = requests.get(self.prime_rate_url)
            prime_data = prime_resp.json()
            
            # Download 5-year mortgage rate
            mortgage_resp = requests.get(self.mortgage_5yr_url)
            mortgage_data = mortgage_resp.json()
            
            # Extract observations
            overnight_obs = overnight_data.get("observations", [])
            prime_obs = prime_data.get("observations", [])
            mortgage_obs = mortgage_data.get("observations", [])
            
            # Create DataFrames for each rate
            overnight_df = pd.DataFrame(overnight_obs)
            prime_df = pd.DataFrame(prime_obs)
            mortgage_df = pd.DataFrame(mortgage_obs)
            
            # Extract observations with proper value access
            # The Bank of Canada API returns JSON in this format:
            # {"observations": [{"d": "2000-01-01", "V39079": {"v": "5.75"}, ...}, ...]}
            
            # For overnight rate
            overnight_df = pd.DataFrame()
            try:
                overnight_df["date"] = [item["d"] for item in overnight_obs]
                overnight_df["overnight_rate"] = [item["V39079"]["v"] for item in overnight_obs]
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing overnight rate data: {e}")
                logger.debug(f"Sample overnight data: {overnight_obs[:1] if overnight_obs else 'No data'}")
                overnight_df = pd.DataFrame(columns=["date", "overnight_rate"])
            
            # For prime rate
            prime_df = pd.DataFrame()
            try:
                prime_df["date"] = [item["d"] for item in prime_obs]
                prime_df["prime_rate"] = [item["V80691311"]["v"] for item in prime_obs]
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing prime rate data: {e}")
                logger.debug(f"Sample prime data: {prime_obs[:1] if prime_obs else 'No data'}")
                prime_df = pd.DataFrame(columns=["date", "prime_rate"])
            
            # For mortgage rate
            mortgage_df = pd.DataFrame()
            try:
                mortgage_df["date"] = [item["d"] for item in mortgage_obs]
                mortgage_df["mortgage_5yr_rate"] = [item["V122521"]["v"] for item in mortgage_obs]
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing mortgage rate data: {e}")
                logger.debug(f"Sample mortgage data: {mortgage_obs[:1] if mortgage_obs else 'No data'}")
                mortgage_df = pd.DataFrame(columns=["date", "mortgage_5yr_rate"])
            
            # Merge DataFrames on date
            rates_df = pd.merge(overnight_df, prime_df, on="date", how="outer")
            rates_df = pd.merge(rates_df, mortgage_df, on="date", how="outer")
            
            return rates_df
        except Exception as e:
            logger.error(f"Error downloading Bank of Canada rates: {e}")
            return pd.DataFrame()
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the Bank of Canada rates data.
        
        Args:
            df: DataFrame containing the raw downloaded data
            
        Returns:
            Preprocessed DataFrame
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to preprocess for Bank of Canada data")
            # Create a minimal DataFrame with required columns
            return pd.DataFrame(columns=["year", "month", "date", "overnight_rate", 
                                        "prime_rate", "mortgage_5yr_rate", "date_str"])
        
        # Convert date to datetime
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        
        # Drop rows with invalid dates
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Dropping {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=["date"])
        
        # Sort by date
        df = df.sort_values("date")
        
        # Keep the rates as strings to match the expected format
        # This is important because in the CSV info provided, rates are strings
        rate_cols = ["overnight_rate", "prime_rate", "mortgage_5yr_rate"]
        
        # Add year and month columns
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        
        # For each month, use the most recent rate
        monthly_df = df.groupby(["year", "month"]).last().reset_index()
        
        # Create date in YYYY-MM format
        monthly_df["date_str"] = monthly_df["year"].astype(str) + "-" + monthly_df["month"].astype(str).str.zfill(2)
        
        # Verify data types match the expected CSV format
        monthly_df["year"] = monthly_df["year"].astype("Int64")  # Integer
        monthly_df["month"] = monthly_df["month"].astype("Int64")  # Integer
        monthly_df["date"] = monthly_df["date"].dt.strftime('%Y-%m-%d')  # String
        
        # Ensure rates are strings
        for col in rate_cols:
            if col in monthly_df.columns:
                monthly_df[col] = monthly_df[col].astype(str)
        
        # Print sample data and column dtypes for verification
        logger.info(f"Bank of Canada data dtypes:\n{monthly_df.dtypes}")
        logger.info(f"Sample Bank of Canada data:\n{monthly_df.head(3)}")
        
        return monthly_df


class StatisticsCanadaEconomic(EconomicDataSource):
    """Statistics Canada economic indicators data source."""
    
    def __init__(self):
        """Initialize the Statistics Canada economic indicators data source."""
        super().__init__("Statistics Canada Economic")
        
        # Table IDs for different indicators
        self.tables = {
            "unemployment_rate": "14-10-0287-01",  # Labour force characteristics by province
            "cpi": "18-10-0004-01",  # Consumer Price Index (CPI)
            "new_housing_price": "18-10-0205-01",  # New housing price index
            "population": "17-10-0009-01",  # Population estimates, quarterly
        }
    
    def download(self) -> pd.DataFrame:
        """
        Download economic indicators from Statistics Canada.
        
        Returns:
            DataFrame containing the economic indicators data
        """
        try:
            # Initialize DataFrames for each indicator
            unemployment_df = pd.DataFrame()
            cpi_df = pd.DataFrame()
            housing_price_df = pd.DataFrame()
            population_df = pd.DataFrame()
            
            # For demonstration purposes, we'll simulate downloading these indicators
            # In a real implementation, you would use the Statistics Canada API
            
            # Simulate data for unemployment rate - start from 2015-01-01 to include one more year for lag calculations
            dates = pd.date_range(start="2015-01-01", end="2025-04-30", freq="MS")
            unemployment_df = pd.DataFrame({
                "date": dates,
                "unemployment_rate_ontario": [6.4 + 0.1 * i for i in range(len(dates))],
                "unemployment_rate_toronto": [5.9 + 0.1 * i for i in range(len(dates))],
            })
            
            # Simulate data for CPI - start from 2015-01-01
            cpi_df = pd.DataFrame({
                "date": dates,
                "cpi_all_items": [99.8 + 0.2 * i for i in range(len(dates))],
                "cpi_housing": [99.7 + 0.3 * i for i in range(len(dates))],
            })
            
            # Simulate data for new housing price index - start from 2015-01-01
            housing_price_df = pd.DataFrame({
                "date": dates,
                "new_housing_price_index": [99.6 + 0.4 * i for i in range(len(dates))],
            })
            
            # Simulate data for population estimates - start from 2015-01-01
            quarterly_dates = pd.date_range(start="2015-01-01", end="2025-04-30", freq="QS")
            population_df = pd.DataFrame({
                "date": quarterly_dates,
                "population_ontario": [13990000 + 10000 * i for i in range(len(quarterly_dates))],
                "population_toronto": [5995000 + 5000 * i for i in range(len(quarterly_dates))],
            })
            
            # Merge all indicators into a single DataFrame
            indicators_df = unemployment_df.copy()
            indicators_df = pd.merge(indicators_df, cpi_df, on="date", how="outer")
            indicators_df = pd.merge(indicators_df, housing_price_df, on="date", how="outer")
            indicators_df = pd.merge(indicators_df, population_df, on="date", how="outer")
            
            # Note: In a real implementation, you would handle missing values more carefully
            
            return indicators_df
        except Exception as e:
            logger.error(f"Error downloading Statistics Canada economic indicators: {e}")
            return pd.DataFrame()
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the Statistics Canada economic indicators data.
        
        Args:
            df: DataFrame containing the raw downloaded data
            
        Returns:
            Preprocessed DataFrame
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to preprocess for Statistics Canada data")
            # Create minimal DataFrame with required columns
            return pd.DataFrame(columns=["year", "month", "date", "cpi_all_items", 
                                        "cpi_housing", "new_housing_price_index", "date_str"])
        
        # Ensure date is in proper datetime format
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        
        # Drop rows with invalid dates
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Dropping {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=["date"])
        
        # Sort by date
        df = df.sort_values("date")
        
        # Fill missing values using forward fill for time series data
        df = df.ffill()
        
        # Add year and month columns
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        
        # Calculate year-over-year changes for key indicators
        for col in ["cpi_all_items", "cpi_housing", "new_housing_price_index"]:
            if col in df.columns:
                df[f"{col}_yoy_change"] = df[col].pct_change(periods=12) * 100
        
        # Create date in YYYY-MM format
        df["date_str"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
        
        # Fix data types to match expected format
        df["year"] = df["year"].astype("Int64")  # Integer
        df["month"] = df["month"].astype("Int64")  # Integer
        df["date"] = df["date"].dt.strftime('%Y-%m-%d')  # String
        
        # Convert numeric columns to appropriate types
        numeric_cols = ["cpi_all_items", "cpi_housing", "new_housing_price_index",
                       "unemployment_rate_ontario", "unemployment_rate_toronto"]
        
        for col in numeric_cols:
            if col in df.columns:
                # First convert to float for calculation, then to string for storage
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        # YoY change columns should also be numeric
        yoy_cols = [col for col in df.columns if col.endswith('_yoy_change')]
        for col in yoy_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Print sample data and column dtypes for verification
        logger.info(f"Statistics Canada data dtypes:\n{df.dtypes}")
        logger.info(f"Sample Statistics Canada data:\n{df.head(3)}")
        
        return df


class CMHCHousingData(EconomicDataSource):
    """CMHC housing data source for housing starts, completions, etc."""
    
    def __init__(self):
        """Initialize the CMHC housing data source."""
        super().__init__("CMHC Housing Data")
        
        # CMHC housing data API
        # Note: In a real implementation, you would use the CMHC API
        self.housing_starts_url = "https://www.cmhc-schl.gc.ca/en/professionals/housing-markets-data-and-research/housing-data/data-tables/housing-market-data/housing-starts"
    
    def download(self) -> pd.DataFrame:
        """
        Download housing data from CMHC.
        
        Returns:
            DataFrame containing the housing data
        """
        try:
            # In a real implementation, you would use the CMHC API
            # For demonstration purposes, we'll simulate downloading the data
            
            # Simulate data for housing starts and completions - start from 2015-01-01
            dates = pd.date_range(start="2015-01-01", end="2025-04-30", freq="MS")
            housing_df = pd.DataFrame({
                "date": dates,
                "housing_starts_gta": [1990 + 10 * i for i in range(len(dates))],
                "housing_completions_gta": [1792 + 8 * i for i in range(len(dates))],
                "under_construction_gta": [14980 + 20 * i for i in range(len(dates))],
            })
            
            return housing_df
        except Exception as e:
            logger.error(f"Error downloading CMHC housing data: {e}")
            return pd.DataFrame()
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the CMHC housing data.
        
        Args:
            df: DataFrame containing the raw downloaded data
            
        Returns:
            Preprocessed DataFrame
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to preprocess for CMHC housing data")
            # Create minimal DataFrame with required columns
            return pd.DataFrame(columns=["year", "month", "date", "housing_starts_gta",
                                       "housing_completions_gta", "under_construction_gta", "date_str"])
        
        # Ensure date is in proper datetime format
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        
        # Drop rows with invalid dates
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Dropping {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=["date"])
        
        # Sort by date
        df = df.sort_values("date")
        
        # Ensure numeric columns are actually numeric before calculations
        numeric_cols = ["housing_starts_gta", "housing_completions_gta", "under_construction_gta"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate rolling 3-month average for housing starts
        df["housing_starts_gta_3m_avg"] = df["housing_starts_gta"].rolling(window=3).mean()
        
        # Calculate year-over-year changes
        for col in ["housing_starts_gta", "housing_completions_gta"]:
            df[f"{col}_yoy_change"] = df[col].pct_change(periods=12) * 100
        
        # Calculate supply metrics
        df["starts_to_completion_ratio"] = df["housing_starts_gta"] / df["housing_completions_gta"]
        
        # Add year and month columns
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        
        # Create date in YYYY-MM format
        df["date_str"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
        
        # Fix data types to match expected format
        df["year"] = df["year"].astype("Int64")  # Integer
        df["month"] = df["month"].astype("Int64")  # Integer
        df["date"] = df["date"].dt.strftime('%Y-%m-%d')  # String
        
        # Print sample data and column dtypes for verification
        logger.info(f"CMHC Housing data dtypes:\n{df.dtypes}")
        logger.info(f"Sample CMHC Housing data:\n{df.head(3)}")
        
        return df


# Factory function to get all data sources
def get_all_data_sources() -> List[EconomicDataSource]:
    """
    Get all available economic data sources.
    
    Returns:
        List of economic data sources
    """
    return [
        BankOfCanadaRates(),
        StatisticsCanadaEconomic(),
        CMHCHousingData(),
    ]
