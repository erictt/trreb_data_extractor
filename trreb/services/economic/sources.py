"""
Economic data sources for housing price prediction with real API connections.
"""

import os
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode
import requests
import pandas as pd
from stats_can import StatsCan


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
        # Define required columns for basic structure
        required_cols = ["year", "month", "date_str"]

        # Use cached data if available and not forcing download
        if self.cache_file.exists() and not force_download:
            logger.info(f"Using cached data for {self.name} from {self.cache_file}")
            try:
                # Specify dtype for year/month to avoid issues if they were saved as float
                dtype_map = {"year": object, "month": object}
                df = pd.read_csv(self.cache_file, dtype=dtype_map)

                # Verify essential columns exist in cache
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    logger.warning(
                        f"Cached data for {self.name} is missing columns: {missing_cols}. Forcing download."
                    )
                    return self._download_and_process()

                logger.info(f"Loaded {len(df)} rows for {self.name} from cache")
                # Ensure correct types from cache after reading as object
                if "year" in df.columns:
                    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(
                        "Int64"
                    )
                if "month" in df.columns:
                    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype(
                        "Int64"
                    )
                return df
            except Exception as e:
                logger.error(
                    f"Error reading cached data for {self.name}: {e}. Forcing download."
                )
                return self._download_and_process()

        # Download and process if no cache or force_download is True
        return self._download_and_process()

    def _download_and_process(self) -> pd.DataFrame:
        """Helper method to download, preprocess, and cache data."""
        logger.info(f"Downloading data for {self.name}")
        required_cols = ["year", "month", "date_str"]
        empty_df = pd.DataFrame(columns=required_cols).astype(
            {"year": "Int64", "month": "Int64", "date_str": "object"}
        )

        try:
            raw_df = self.download()

            if raw_df is None or raw_df.empty:
                logger.warning(f"Download returned no data for {self.name}")
                return empty_df

            processed_df = self.preprocess(raw_df)

            missing_cols = [
                col for col in required_cols if col not in processed_df.columns
            ]
            if missing_cols:
                logger.error(
                    f"Processed data for {self.name} is missing required columns: {missing_cols}"
                )
                if "date_str" in processed_df.columns:
                    try:
                        processed_df["date_str"] = processed_df["date_str"].astype(str)
                        processed_df["year"] = pd.to_datetime(
                            processed_df["date_str"] + "-01", errors="coerce"
                        ).dt.year.astype("Int64")
                        processed_df["month"] = pd.to_datetime(
                            processed_df["date_str"] + "-01", errors="coerce"
                        ).dt.month.astype("Int64")
                        logger.info(
                            f"Created 'year' and 'month' columns from 'date_str' for {self.name}"
                        )
                        missing_cols = [
                            col
                            for col in required_cols
                            if col not in processed_df.columns
                        ]
                    except Exception as fix_e:
                        logger.error(
                            f"Could not automatically create year/month columns for {self.name}: {fix_e}"
                        )

                if missing_cols:
                    logger.error(
                        f"Returning empty DataFrame for {self.name} due to missing columns: {missing_cols}"
                    )
                    return empty_df

            try:
                df_to_save = processed_df.copy()
                if "year" in df_to_save.columns:
                    df_to_save["year"] = df_to_save["year"].astype(object)
                if "month" in df_to_save.columns:
                    df_to_save["month"] = df_to_save["month"].astype(object)

                df_to_save.to_csv(self.cache_file, index=False)
                logger.info(
                    f"Cached {len(processed_df)} rows of data for {self.name} to {self.cache_file}"
                )
            except Exception as e:
                logger.error(f"Error caching data for {self.name}: {e}")

            if "year" in processed_df.columns:
                processed_df["year"] = pd.to_numeric(
                    processed_df["year"], errors="coerce"
                ).astype("Int64")
            if "month" in processed_df.columns:
                processed_df["month"] = pd.to_numeric(
                    processed_df["month"], errors="coerce"
                ).astype("Int64")

            return processed_df

        except Exception as e:
            logger.error(
                f"An error occurred during download/processing for {self.name}: {e}",
                exc_info=True,
            )
            return empty_df


class BankOfCanadaRates(EconomicDataSource):
    """Bank of Canada interest rates data source."""

    def __init__(self):
        """Initialize the Bank of Canada interest rates data source."""
        super().__init__("Bank of Canada Rates")

        self.base_url = "https://www.bankofcanada.ca/valet/observations"
        self.series = {
            "overnight_rate": "V122514",
            "prime_rate": "V80691311",
            "mortgage_5yr_rate": "V122521",
        }
        self.start_date = "2015-01-01"
        self.end_date = datetime.now().strftime("%Y-%m-%d")

    def download(self) -> pd.DataFrame:
        """
        Download interest rates data from the Bank of Canada.
        WARNING: SSL verification is disabled in this version.
        """
        all_rates_data = []
        dates = set()

        for rate_name, series_id in self.series.items():
            api_url = f"{self.base_url}/{series_id}/json"
            params = {"start_date": self.start_date, "end_date": self.end_date}
            full_url = f"{api_url}?{urlencode(params)}"
            logger.info(f"Fetching {rate_name} data from {full_url}")

            try:
                logger.warning(
                    f"Disabling SSL verification for Bank of Canada request ({rate_name}). THIS IS INSECURE."
                )
                response = requests.get(full_url, timeout=30, verify=False)
                response.raise_for_status()

                data = response.json()
                observations = data.get("observations", [])

                if not observations:
                    logger.warning(
                        f"No observations found for {rate_name} ({series_id})"
                    )
                    continue

                rate_data = []
                for item in observations:
                    date_str = item.get("d")
                    value_info = item.get(series_id)
                    value = value_info.get("v") if value_info else None

                    if date_str and value is not None:
                        try:
                            value_float = float(value)
                            rate_data.append({"date": date_str, rate_name: value_float})
                            dates.add(date_str)
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                f"Could not convert value '{value}' to float for {rate_name} on date {date_str}: {e}"
                            )
                    else:
                        logger.warning(
                            f"Missing date or value for {rate_name} in item: {item}"
                        )

                all_rates_data.extend(rate_data)
                logger.info(
                    f"Successfully fetched {len(rate_data)} records for {rate_name}"
                )
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch {rate_name} data from {full_url}: {e}")
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON response for {rate_name} from {full_url}: {e}"
                )
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred fetching {rate_name}: {e}",
                    exc_info=True,
                )

        if not all_rates_data:
            logger.error("No data fetched from Bank of Canada for any series.")
            return pd.DataFrame()

        df = pd.DataFrame(all_rates_data)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        if df.empty:
            logger.error("Bank of Canada data is empty after date conversion.")
            return pd.DataFrame()

        try:
            grouped_df = df.groupby("date").last().reset_index()
            logger.info(
                f"Successfully grouped Bank of Canada data, resulting in {len(grouped_df)} records"
            )
            return grouped_df
        except Exception as e:
            logger.error(f"Error grouping Bank of Canada data: {e}")
            return pd.DataFrame()

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the Bank of Canada rates data.
        """
        required_cols = ["year", "month", "date_str"]
        rate_cols = list(self.series.keys())
        expected_cols = required_cols + rate_cols

        if df.empty:
            logger.warning(
                "Empty DataFrame passed to preprocess for Bank of Canada data"
            )
            return pd.DataFrame(columns=expected_cols).astype(
                {"year": "Int64", "month": "Int64", "date_str": "object"}
            )

        if "date" not in df.columns or not pd.api.types.is_datetime64_any_dtype(
            df["date"]
        ):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            if df.empty:
                logger.warning(
                    "No valid dates found after conversion in Bank of Canada preprocess."
                )
                return pd.DataFrame(columns=expected_cols).astype(
                    {"year": "Int64", "month": "Int64", "date_str": "object"}
                )

        df = df.sort_values("date")
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        df = df.set_index("date")
        fill_cols = [col for col in rate_cols if col in df.columns]
        if fill_cols:
            df[fill_cols] = df[fill_cols].ffill()
        else:
            logger.warning("No rate columns found in BoC DataFrame before resampling.")

        monthly_df = df.resample("M").last()
        monthly_df = monthly_df.reset_index()

        monthly_df["year"] = monthly_df["date"].dt.year
        monthly_df["month"] = monthly_df["date"].dt.month
        monthly_df["date_str"] = (
            monthly_df["year"].astype(str)
            + "-"
            + monthly_df["month"].astype(str).str.zfill(2)
        )

        monthly_df["year"] = monthly_df["year"].astype("Int64")
        monthly_df["month"] = monthly_df["month"].astype("Int64")

        for col in rate_cols:
            if col in monthly_df.columns:
                monthly_df[col] = pd.to_numeric(
                    monthly_df[col], errors="coerce"
                ).astype("float64")
            else:
                logger.warning(
                    f"Rate column '{col}' not found in downloaded BoC data after resampling. Adding as NaN."
                )
                monthly_df[col] = pd.NA

        final_cols = required_cols + [
            col for col in rate_cols if col in monthly_df.columns
        ]
        monthly_df = monthly_df[final_cols]

        logger.info(
            f"Bank of Canada data preprocessed into {len(monthly_df)} monthly records."
        )
        logger.debug(f"Bank of Canada data dtypes:\n{monthly_df.dtypes}")
        logger.debug(f"Sample Bank of Canada data:\n{monthly_df.head(3)}")

        return monthly_df


class StatisticsCanadaEconomic(EconomicDataSource):
    """Statistics Canada economic indicators data source using stats-can library."""

    def __init__(self):
        """Initialize the Statistics Canada economic indicators data source."""
        super().__init__("Statistics Canada Economic")

        # Define indicators using their Vector IDs
        self.indicators = {
            "unemployment_rate_ontario": "v2062815",
            "unemployment_rate_toronto": "v2062856",
            "cpi_all_items_ontario": "v41690974",
            "cpi_shelter_ontario": "v41691006",
            "nhpi_toronto": "v111955442",
        }
        # Number of latest periods to fetch (approx 30 years of monthly data)
        self.num_periods = 360

    def download(self) -> pd.DataFrame:
        """
        Download economic indicators from Statistics Canada using stats-can library.
        """

        if not self.indicators:
            logger.warning("No StatCan indicators defined.")
            return pd.DataFrame()

        # Initialize stats-can client
        sc = StatsCan()

        # Prepare list of vector IDs
        vector_ids = list(self.indicators.values())
        logger.info(
            f"Fetching StatCan data for {len(vector_ids)} vectors: {vector_ids}"
        )

        try:
            # Fetch data for all vectors at once
            df = sc.vectors_to_df(vectors=vector_ids, periods=self.num_periods)

            if df is None or df.empty:
                logger.error("No data returned from stats-can for requested vectors.")
                return pd.DataFrame()

            # Reset index to get 'REF_DATE' as a column
            df = df.reset_index()

            # Rename columns: 'REF_DATE' to 'date' and vector IDs to indicator names
            rename_dict = {"REF_DATE": "date"}
            for vec_id, indicator_name in self.indicators.items():
                rename_dict[vec_id] = indicator_name
            df = df.rename(columns=rename_dict)

            # Ensure 'date' is datetime
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            if df.empty:
                logger.error("StatCan data is empty after date conversion.")
                return pd.DataFrame()

            # Select only the date and indicator columns
            expected_cols = ["date"] + list(self.indicators.keys())
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                logger.warning(
                    f"Missing expected columns in StatCan data: {missing_cols}"
                )
                for col in missing_cols:
                    if col != "date":
                        df[col] = pd.NA  # Add missing indicator columns as NA

            # Ensure indicator columns are numeric
            for col in self.indicators.keys():
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

            # Sort by date
            df = df.sort_values("date").reset_index(drop=True)
            logger.info(f"Successfully downloaded StatCan data with shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(
                f"Error fetching StatCan data using stats-can: {e}", exc_info=True
            )
            return pd.DataFrame()

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the Statistics Canada economic indicators data.
        """
        required_cols = ["year", "month", "date_str"]
        indicator_cols = list(self.indicators.keys())
        expected_cols = required_cols + indicator_cols

        if df.empty:
            logger.warning(
                "Empty DataFrame passed to preprocess for Statistics Canada data"
            )
            return pd.DataFrame(columns=expected_cols).astype(
                {"year": "Int64", "month": "Int64", "date_str": "object"}
            )

        if "date" not in df.columns or not pd.api.types.is_datetime64_any_dtype(
            df["date"]
        ):
            logger.error(
                "Statistics Canada preprocess requires a 'date' column of datetime type."
            )
            return pd.DataFrame(columns=expected_cols).astype(
                {"year": "Int64", "month": "Int64", "date_str": "object"}
            )

        df = df.sort_values("date").reset_index(drop=True)
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["date_str"] = (
            df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
        )

        df["year"] = df["year"].astype("Int64")
        df["month"] = df["month"].astype("Int64")

        for col in indicator_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
            else:
                logger.warning(
                    f"Indicator column '{col}' missing in StatCan preprocess. Adding as NaN."
                )
                df[col] = pd.NA

        final_cols = required_cols + [
            col for col in indicator_cols if col in df.columns
        ]
        df = df[final_cols]

        logger.info(
            f"Statistics Canada data preprocessed into {len(df)} monthly records."
        )
        logger.debug(f"Statistics Canada data dtypes:\n{df.dtypes}")
        logger.debug(f"Sample Statistics Canada data:\n{df.head(3)}")

        return df


def get_all_data_sources() -> List[EconomicDataSource]:
    """
    Get all available economic data sources.

    Returns:
        List of economic data sources instances.
    """
    return [
        BankOfCanadaRates(),
        StatisticsCanadaEconomic(),
    ]


if __name__ == "__main__":
    logger.info("--- Testing Economic Data Sources ---")

    if not ECONOMIC_DIR.exists():
        ECONOMIC_DIR.mkdir(parents=True)

    sources = get_all_data_sources()
    all_data = {}

    for source in sources:
        logger.info(f"\n--- Getting data for: {source.name} ---")
        data_df = source.get_data(force_download=True)
        if data_df is not None and not data_df.empty:
            logger.info(
                f"Successfully retrieved data for {source.name}. Shape: {data_df.shape}"
            )
            logger.info(f"Columns: {', '.join(data_df.columns)}")
            logger.info(f"Sample data:\n{data_df.head()}")
            all_data[source.name] = data_df
        else:
            logger.warning(
                f"Failed to retrieve data for {source.name} or data was empty."
            )

    logger.info("\n--- Economic Data Source Testing Complete ---")

    if "Statistics Canada Economic" in all_data:
        statcan_df = all_data["Statistics Canada Economic"]
        if not statcan_df.empty:
            print("\n--- Sample Statistics Canada Data ---")
            print(statcan_df.head())
            print(
                f"\nDate Range: {statcan_df['date_str'].min()} to {statcan_df['date_str'].max()}"
            )
            print("\nMissing values per column:")
            print(statcan_df.isnull().sum())
        else:
            print("\n--- Statistics Canada Data was empty ---")
    else:
        print("\n--- Statistics Canada Data not found in results ---")

    if "Bank of Canada Rates" in all_data:
        boc_df = all_data["Bank of Canada Rates"]
        if not boc_df.empty:
            print("\n--- Sample Bank of Canada Data ---")
            print(boc_df.head())
            print(
                f"\nDate Range: {boc_df['date_str'].min()} to {boc_df['date_str'].max()}"
            )
            print("\nMissing values per column:")
            print(boc_df.isnull().sum())
        else:
            print("\n--- Bank of Canada Data was empty ---")
    else:
        print("\n--- Bank of Canada Data not found in results ---")
