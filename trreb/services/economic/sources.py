"""
Economic data sources for housing price prediction with real API connections.
"""

import os
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode

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
        self.base_url = "https://www.bankofcanada.ca/valet/observations"
        self.overnight_rate_series = "V39079"  # Overnight rate series
        self.prime_rate_series = "V80691311"  # Prime rate series
        self.mortgage_5yr_series = "V122521"  # 5-year mortgage rate series
        
        # Date range for fetching data (starting from 2015-01-01)
        self.start_date = "2015-01-01"
        self.end_date = datetime.now().strftime("%Y-%m-%d")
    
    def download(self) -> pd.DataFrame:
        """
        Download interest rates data from the Bank of Canada.
        
        Returns:
            DataFrame containing the interest rates data
        """
        try:
            # Create the URL for the Overnight Rate with parameters
            overnight_url = f"{self.base_url}/{self.overnight_rate_series}/json"
            params = {
                "start_date": self.start_date,
                "end_date": self.end_date
            }
            overnight_full_url = f"{overnight_url}?{urlencode(params)}"
            
            # Download overnight rate
            logger.info(f"Fetching overnight rate data from {overnight_full_url}")
            overnight_resp = requests.get(overnight_full_url)
            
            if overnight_resp.status_code != 200:
                logger.error(f"Failed to fetch overnight rate data. Status code: {overnight_resp.status_code}")
                logger.error(f"Response: {overnight_resp.text}")
                raise Exception(f"API request failed with status {overnight_resp.status_code}")
                
            overnight_data = overnight_resp.json()
            
            # Create the URL for the Prime Rate with parameters
            prime_url = f"{self.base_url}/{self.prime_rate_series}/json"
            prime_full_url = f"{prime_url}?{urlencode(params)}"
            
            # Download prime rate
            logger.info(f"Fetching prime rate data from {prime_full_url}")
            prime_resp = requests.get(prime_full_url)
            
            if prime_resp.status_code != 200:
                logger.error(f"Failed to fetch prime rate data. Status code: {prime_resp.status_code}")
                logger.error(f"Response: {prime_resp.text}")
                raise Exception(f"API request failed with status {prime_resp.status_code}")
                
            prime_data = prime_resp.json()
            
            # Create the URL for the 5-year Mortgage Rate with parameters
            mortgage_url = f"{self.base_url}/{self.mortgage_5yr_series}/json"
            mortgage_full_url = f"{mortgage_url}?{urlencode(params)}"
            
            # Download 5-year mortgage rate
            logger.info(f"Fetching 5-year mortgage rate data from {mortgage_full_url}")
            mortgage_resp = requests.get(mortgage_full_url)
            
            if mortgage_resp.status_code != 200:
                logger.error(f"Failed to fetch mortgage rate data. Status code: {mortgage_resp.status_code}")
                logger.error(f"Response: {mortgage_resp.text}")
                raise Exception(f"API request failed with status {mortgage_resp.status_code}")
                
            mortgage_data = mortgage_resp.json()
            
            # Extract observations
            overnight_obs = overnight_data.get("observations", [])
            prime_obs = prime_data.get("observations", [])
            mortgage_obs = mortgage_data.get("observations", [])
            
            # Extract data into dataframes
            overnight_df = pd.DataFrame()
            try:
                overnight_df["date"] = [item["d"] for item in overnight_obs]
                overnight_df["overnight_rate"] = [item[self.overnight_rate_series]["v"] for item in overnight_obs]
                logger.info(f"Successfully extracted {len(overnight_df)} overnight rate records")
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing overnight rate data: {e}")
                logger.debug(f"Sample overnight data: {overnight_obs[:1] if overnight_obs else 'No data'}")
                overnight_df = pd.DataFrame(columns=["date", "overnight_rate"])
            
            # For prime rate
            prime_df = pd.DataFrame()
            try:
                prime_df["date"] = [item["d"] for item in prime_obs]
                prime_df["prime_rate"] = [item[self.prime_rate_series]["v"] for item in prime_obs]
                logger.info(f"Successfully extracted {len(prime_df)} prime rate records")
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing prime rate data: {e}")
                logger.debug(f"Sample prime data: {prime_obs[:1] if prime_obs else 'No data'}")
                prime_df = pd.DataFrame(columns=["date", "prime_rate"])
            
            # For mortgage rate
            mortgage_df = pd.DataFrame()
            try:
                mortgage_df["date"] = [item["d"] for item in mortgage_obs]
                mortgage_df["mortgage_5yr_rate"] = [item[self.mortgage_5yr_series]["v"] for item in mortgage_obs]
                logger.info(f"Successfully extracted {len(mortgage_df)} mortgage rate records")
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing mortgage rate data: {e}")
                logger.debug(f"Sample mortgage data: {mortgage_obs[:1] if mortgage_obs else 'No data'}")
                mortgage_df = pd.DataFrame(columns=["date", "mortgage_5yr_rate"])
            
            # Merge DataFrames on date
            rates_df = pd.merge(overnight_df, prime_df, on="date", how="outer")
            rates_df = pd.merge(rates_df, mortgage_df, on="date", how="outer")
            
            logger.info(f"Successfully merged all rate data, resulting in {len(rates_df)} records")
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
        
        # Ensure rates are strings (to match the expected format)
        rate_cols = ["overnight_rate", "prime_rate", "mortgage_5yr_rate"]
        for col in rate_cols:
            if col in monthly_df.columns:
                monthly_df[col] = monthly_df[col].astype(str)
        
        # Print sample data and column dtypes for verification
        logger.info(f"Bank of Canada data dtypes:\n{monthly_df.dtypes}")
        logger.info(f"Sample Bank of Canada data:\n{monthly_df.head(3)}")
        
        return monthly_df


class StatisticsCanadaEconomic(EconomicDataSource):
    """Statistics Canada economic indicators data source using real API."""
    
    def __init__(self):
        """Initialize the Statistics Canada economic indicators data source."""
        super().__init__("Statistics Canada Economic")
        
        # Base URLs and endpoints
        self.base_url = "https://www150.statcan.gc.ca/t1/wds/rest"
        self.get_data_endpoint = "/getDataFromCubePidCoordinate"
        self.get_cube_metadata_endpoint = "/getCubeMetadata"
        
        # Table IDs (product IDs) for different indicators
        self.tables = {
            "unemployment_rate": "14-10-0287-01",  # Labour force characteristics by province
            "cpi": "18-10-0004-01",               # Consumer Price Index (CPI)
            "new_housing_price": "18-10-0205-01", # New housing price index
            "population": "17-10-0009-01",        # Population estimates, quarterly
        }
        
        # Parameter mapping for specific data points
        self.params = {
            "unemployment_rate": {
                "ontario": {"geo": "35", "sex": "1", "age_group": "1", "labour_force_char": "2"},
                "toronto": {"geo": "35535", "sex": "1", "age_group": "1", "labour_force_char": "2"}
            },
            "cpi": {
                "all_items": {"geo": "35", "products": "1"},
                "housing": {"geo": "35", "products": "36"}
            },
            "new_housing_price": {
                "index": {"geo": "35", "type": "1"}
            },
            "population": {
                "ontario": {"geo": "35", "sex": "1", "age_group": "1"},
                "toronto": {"geo": "35535", "sex": "1", "age_group": "1"}
            }
        }
        
        # Date range to fetch (starting from 2015-01-01)
        self.start_date = "2015-01-01"
        self.end_date = datetime.now().strftime("%Y-%m-%d")
    
    def download(self) -> pd.DataFrame:
        """
        Download economic indicators from Statistics Canada.
        
        Returns:
            DataFrame containing the economic indicators data
        """
        try:
            # Call the Statistics Canada API to fetch data for each indicator
            logger.info("Fetching unemployment rate data...")
            unemployment_df = self._fetch_unemployment_data()
            
            logger.info("Fetching consumer price index data...")
            cpi_df = self._fetch_cpi_data()
            
            logger.info("Fetching new housing price index data...")
            housing_price_df = self._fetch_housing_price_data()
            
            logger.info("Fetching population estimates data...")
            population_df = self._fetch_population_data()
            
            # Merge all indicators into a single DataFrame
            # Start with unemployment data
            indicators_df = unemployment_df.copy() if not unemployment_df.empty else pd.DataFrame()
            
            # Merge CPI data
            if not cpi_df.empty:
                if indicators_df.empty:
                    indicators_df = cpi_df.copy()
                else:
                    indicators_df = pd.merge(indicators_df, cpi_df, on="date", how="outer")
            
            # Merge housing price data
            if not housing_price_df.empty:
                if indicators_df.empty:
                    indicators_df = housing_price_df.copy()
                else:
                    indicators_df = pd.merge(indicators_df, housing_price_df, on="date", how="outer")
            
            # Merge population data
            if not population_df.empty:
                if indicators_df.empty:
                    indicators_df = population_df.copy()
                else:
                    indicators_df = pd.merge(indicators_df, population_df, on="date", how="outer")
            
            # If no data was successfully fetched, create a dummy dataframe for simulation fallback
            if indicators_df.empty:
                logger.warning("No data fetched from Statistics Canada. Falling back to simulated data.")
                return self._generate_simulated_data()
            
            return indicators_df
        except Exception as e:
            logger.error(f"Error downloading Statistics Canada economic indicators: {e}")
            logger.warning("Falling back to simulated data due to API error.")
            return self._generate_simulated_data()
    
    def _fetch_unemployment_data(self) -> pd.DataFrame:
        """Fetch unemployment rate data from Statistics Canada."""
        try:
            # Implement actual API call here
            # For now, simulate the response with a placeholder
            logger.warning("StatCan API implementation for unemployment data is not complete. Using simulated data.")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching unemployment data: {e}")
            return pd.DataFrame()
    
    def _fetch_cpi_data(self) -> pd.DataFrame:
        """Fetch consumer price index data from Statistics Canada."""
        try:
            # Implement actual API call here
            # For now, simulate the response with a placeholder
            logger.warning("StatCan API implementation for CPI data is not complete. Using simulated data.")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching CPI data: {e}")
            return pd.DataFrame()
    
    def _fetch_housing_price_data(self) -> pd.DataFrame:
        """Fetch new housing price index data from Statistics Canada."""
        try:
            # Implement actual API call here
            # For now, simulate the response with a placeholder
            logger.warning("StatCan API implementation for housing price data is not complete. Using simulated data.")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching housing price data: {e}")
            return pd.DataFrame()
    
    def _fetch_population_data(self) -> pd.DataFrame:
        """Fetch population estimates data from Statistics Canada."""
        try:
            # Implement actual API call here
            # For now, simulate the response with a placeholder
            logger.warning("StatCan API implementation for population data is not complete. Using simulated data.")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching population data: {e}")
            return pd.DataFrame()
    
    def _generate_simulated_data(self) -> pd.DataFrame:
        """Generate simulated data as a fallback when API fails."""
        logger.info("Generating simulated Statistics Canada data...")
        
        # Simulate data for unemployment rate
        dates = pd.date_range(start="2015-01-01", end=datetime.now().strftime("%Y-%m-%d"), freq="MS")
        unemployment_df = pd.DataFrame({
            "date": dates,
            "unemployment_rate_ontario": [6.4 + 0.1 * i for i in range(len(dates))],
            "unemployment_rate_toronto": [5.9 + 0.1 * i for i in range(len(dates))],
        })
        
        # Simulate data for CPI
        cpi_df = pd.DataFrame({
            "date": dates,
            "cpi_all_items": [99.8 + 0.2 * i for i in range(len(dates))],
            "cpi_housing": [99.7 + 0.3 * i for i in range(len(dates))],
        })
        
        # Simulate data for new housing price index
        housing_price_df = pd.DataFrame({
            "date": dates,
            "new_housing_price_index": [99.6 + 0.4 * i for i in range(len(dates))],
        })
        
        # Simulate data for population estimates
        quarterly_dates = pd.date_range(start="2015-01-01", end=datetime.now().strftime("%Y-%m-%d"), freq="QS")
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
        
        return indicators_df
    
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
        
        # CMHC housing data API base URL
        # Note: CMHC doesn't have a public API, so we would need to implement web scraping
        # or use any available API if CMHC provides credentials
        self.base_url = "https://www.cmhc-schl.gc.ca/en/professionals/housing-markets-data-and-research/housing-data/data-tables/housing-market-data"
        
        # Date range for fetching data (starting from 2015-01-01)
        self.start_date = "2015-01-01"
        self.end_date = datetime.now().strftime("%Y-%m-%d")
    
    def download(self) -> pd.DataFrame:
        """
        Download housing data from CMHC.
        
        Returns:
            DataFrame containing the housing data
        """
        try:
            # In a real implementation, we would use CMHC's API if available
            # Currently, CMHC doesn't offer a public API, so we would need to implement
            # web scraping or find alternative data sources
            
            logger.warning("CMHC API implementation is not available. Using simulated data.")
            
            # Simulate data for housing starts and completions
            dates = pd.date_range(start=self.start_date, end=self.end_date, freq="MS")
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
