"""
Economic data sources for housing price prediction with real API connections.

WARNING: This version disables SSL verification (verify=False) for HTTPS requests.
         This is INSECURE and should only be used for temporary testing in a
         trusted environment. Do NOT use this in production. The recommended
         solution is to fix the underlying SSL certificate issue on your system
         (e.g., update CA certificates).
"""

import os
import json  # <--- Import json library
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode
import requests
import pandas as pd

# import certifi # <-- No longer strictly needed if verify=False, but keep if other code uses it
import urllib3  # <-- Import urllib3 to disable warnings

# Disable InsecureRequestWarning when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
                # Read these as object first, then convert to Int64 after handling potential NA strings
                dtype_map = {"year": object, "month": object}
                df = pd.read_csv(self.cache_file, dtype=dtype_map)

                # Verify essential columns exist in cache
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    logger.warning(
                        f"Cached data for {self.name} is missing columns: {missing_cols}. Forcing download."
                    )
                    return (
                        self._download_and_process()
                    )  # Force download if cache is invalid

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
                return (
                    self._download_and_process()
                )  # Fall back to downloading if cache read fails

        # Download and process if no cache or force_download is True
        return self._download_and_process()

    def _download_and_process(self) -> pd.DataFrame:
        """Helper method to download, preprocess, and cache data."""
        logger.info(f"Downloading data for {self.name}")
        required_cols = ["year", "month", "date_str"]
        # Ensure the empty DataFrame has the correct initial types
        empty_df = pd.DataFrame(columns=required_cols).astype(
            {"year": "Int64", "month": "Int64", "date_str": "object"}
        )

        try:
            raw_df = self.download()

            if raw_df is None or raw_df.empty:
                logger.warning(f"Download returned no data for {self.name}")
                return empty_df  # Return empty df with standard columns

            processed_df = self.preprocess(raw_df)

            # Verify essential columns exist after processing
            missing_cols = [
                col for col in required_cols if col not in processed_df.columns
            ]
            if missing_cols:
                logger.error(
                    f"Processed data for {self.name} is missing required columns: {missing_cols}"
                )
                # Attempt to fix common issue: create date columns from date_str if possible
                if "date_str" in processed_df.columns:
                    try:
                        # Ensure date_str is string before adding '-01'
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
                        ]  # Recheck
                    except Exception as fix_e:
                        logger.error(
                            f"Could not automatically create year/month columns for {self.name}: {fix_e}"
                        )

                if missing_cols:  # If still missing after trying to fix
                    logger.error(
                        f"Returning empty DataFrame for {self.name} due to missing columns: {missing_cols}"
                    )
                    return empty_df

            # Cache data
            try:
                # Create a copy for saving to avoid modifying the df returned
                df_to_save = processed_df.copy()
                # Convert Int64 columns to object type before saving to handle NA correctly in CSV
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

            # Ensure types are correct (Int64) in the DataFrame being returned
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
            return empty_df  # Return empty df with standard columns on error


class BankOfCanadaRates(EconomicDataSource):
    """Bank of Canada interest rates data source."""

    def __init__(self):
        """Initialize the Bank of Canada interest rates data source."""
        super().__init__("Bank of Canada Rates")

        # API URLs and Series IDs
        self.base_url = "https://www.bankofcanada.ca/valet/observations"
        self.series = {
            "overnight_rate": "V122514",  # TARGET FOR THE OVERNIGHT RATE (adjusted daily series)
            "prime_rate": "V80691311",  # Prime rate (monthly avg) - Use V121700 for daily if needed
            "mortgage_5yr_rate": "V122521",  # 5-year conventional mortgage rate (monthly avg)
        }

        # Date range for fetching data (starting from 2015-01-01)
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
                # ---!!! INSECURE: Disabling SSL Verification !!!---
                logger.warning(
                    f"Disabling SSL verification for Bank of Canada request ({rate_name}). THIS IS INSECURE."
                )
                response = requests.get(full_url, timeout=30, verify=False)
                # ----------------------------------------------------

                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

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
                            # Attempt to convert value to float, handle potential errors
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
                time.sleep(0.5)  # Small delay between requests

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

        # Create a DataFrame from the collected data
        df = pd.DataFrame(all_rates_data)

        # Convert date column to datetime objects
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])  # Drop rows where date conversion failed

        if df.empty:
            logger.error("Bank of Canada data is empty after date conversion.")
            return pd.DataFrame()

        # Group by date and take the last value for each rate
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

        # Ensure 'date' column is datetime
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

        # Sort by date
        df = df.sort_values("date")

        # Add year and month columns
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        # Resample to get the last available rate for each month
        # Set date as index for resampling
        df = df.set_index("date")

        # Forward fill missing values BEFORE resampling
        fill_cols = [col for col in rate_cols if col in df.columns]
        if fill_cols:
            df[fill_cols] = df[fill_cols].ffill()
        else:
            logger.warning("No rate columns found in BoC DataFrame before resampling.")

        # Resample to Month End ('M') and take last obs
        monthly_df = df.resample("M").last()

        # Reset index to get date back as a column
        monthly_df = monthly_df.reset_index()

        # Adjust year and month based on the month-end date
        monthly_df["year"] = monthly_df["date"].dt.year
        monthly_df["month"] = monthly_df["date"].dt.month

        # Create date_str in YYYY-MM format
        monthly_df["date_str"] = (
            monthly_df["year"].astype(str)
            + "-"
            + monthly_df["month"].astype(str).str.zfill(2)
        )

        # Convert types
        monthly_df["year"] = monthly_df["year"].astype("Int64")
        monthly_df["month"] = monthly_df["month"].astype("Int64")

        # Ensure rate columns are float, handle potential all-NaN columns
        for col in rate_cols:
            if col in monthly_df.columns:
                # Use float64 for numeric columns that might contain NA
                monthly_df[col] = pd.to_numeric(
                    monthly_df[col], errors="coerce"
                ).astype("float64")
            else:
                logger.warning(
                    f"Rate column '{col}' not found in downloaded BoC data after resampling. Adding as NaN."
                )
                monthly_df[col] = pd.NA

        # Select and order final columns
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
    """Statistics Canada economic indicators data source using WDS API (Vector IDs)."""

    def __init__(self):
        """Initialize the Statistics Canada economic indicators data source."""
        super().__init__("Statistics Canada Economic")

        # Base URLs and endpoints
        self.base_url = "https://www150.statcan.gc.ca/t1/wds/rest"
        # Endpoint for fetching data using Vector IDs
        self.get_data_endpoint = "/getDataFromVectorsAndLatestNPeriods"

        # Define indicators using their Vector IDs
        self.indicators = {
            "unemployment_rate_ontario": "v2062815",
            "unemployment_rate_toronto": "v2062856",
            "cpi_all_items_ontario": "v41690974",
            "cpi_shelter_ontario": "v41691006",
            "nhpi_toronto": "v111955442",
        }
        # Number of latest periods to fetch
        self.num_periods = 360  # Approx 30 years of monthly data

        # Create reverse mapping from vector ID to indicator name for parsing response
        self.vector_to_indicator = {v: k for k, v in self.indicators.items()}

    def download(self) -> pd.DataFrame:
        """
        Download economic indicators from Statistics Canada using Vector IDs in a single request.
        WARNING: SSL verification is disabled in this version.
        """
        if not self.indicators:
            logger.warning("No StatCan indicators defined.")
            return pd.DataFrame()

        # Prepare payload with all requested vectors
        payload_list = [
            {"vectorId": vec_id, "latestN": self.num_periods}
            for vec_id in self.indicators.values()
        ]

        # Manually serialize the payload to a JSON string
        payload_json_string = json.dumps(payload_list)

        url = f"{self.base_url}{self.get_data_endpoint}"
        logger.info(f"Fetching StatCan data for {len(payload_list)} vectors from {url}")
        # Explicitly set Content-Type header
        headers = {"Content-Type": "application/json"}

        try:
            # ---!!! INSECURE: Disabling SSL Verification !!!---
            logger.warning(
                f"Disabling SSL verification for StatCan request. THIS IS INSECURE."
            )
            response = requests.post(
                url,
                data=payload_json_string,  # Send the manually serialized string
                headers=headers,
                timeout=120,  # Increased timeout
                verify=False,
            )
            # ----------------------------------------------------

            response.raise_for_status()  # Check for HTTP errors (4xx, 5xx)

            response_data = response.json()

            # Check if response is a list (expected)
            if not isinstance(response_data, list):
                logger.error(
                    f"StatCan API response is not a list as expected. Response type: {type(response_data)}. Response: {str(response_data)[:500]}"
                )
                return pd.DataFrame()

            all_vector_dfs = []  # List to hold DataFrames for each vector

            # Process response for each vector
            for vector_response in response_data:
                status = vector_response.get("status")
                vector_object = vector_response.get("object", {})
                vector_id = vector_object.get("vectorId")  # Vector ID from the response

                # Find the originally requested vector ID corresponding to this response part
                req_vector_id = vector_id  # Use the ID from the response object

                if status != "SUCCESS" or not req_vector_id:
                    error_msg = (
                        vector_object
                        if status != "SUCCESS"
                        else "Missing vectorId in response object"
                    )
                    logger.error(
                        f"StatCan API returned non-SUCCESS or invalid object for requested vector (reported ID: {req_vector_id}): {error_msg}"
                    )
                    # Log specific error messages if available
                    if isinstance(error_msg, dict) and "message" in error_msg:
                        msg_lower = error_msg["message"].lower()
                        if "vector(s) provided is not valid" in msg_lower:
                            logger.error(
                                f"INVALID VECTOR ID DETECTED: {req_vector_id}. Please verify the ID."
                            )
                        elif "vector does not exist" in msg_lower:
                            logger.error(
                                f"VECTOR ID DOES NOT EXIST: {req_vector_id}. Please verify the ID."
                            )
                        elif "json syntax error" in msg_lower:
                            logger.error(
                                f"API reported JSON syntax error for vector {req_vector_id}. Payload structure might be wrong despite matching docs."
                            )

                    continue  # Skip this vector and proceed to the next

                # Get indicator name from vector ID using the reverse map
                indicator_name = self.vector_to_indicator.get(req_vector_id)
                if not indicator_name:
                    logger.warning(
                        f"Received data for unexpected Vector ID {req_vector_id}. Skipping."
                    )
                    continue

                data_points = vector_object.get("vectorDataPoint", [])
                if not data_points:
                    logger.warning(
                        f"No data points returned in 'vectorDataPoint' for Vector {req_vector_id} ({indicator_name})."
                    )
                    continue

                # Convert data points to DataFrame
                df = pd.DataFrame(data_points)
                if "refPer" not in df.columns or "value" not in df.columns:
                    logger.error(
                        f"Missing 'refPer' or 'value' column for Vector {req_vector_id} ({indicator_name}). Columns: {df.columns}"
                    )
                    continue

                df = df[["refPer", "value"]]
                df.rename(
                    columns={"refPer": "date", "value": indicator_name}, inplace=True
                )  # Rename value column immediately

                # Convert date and value
                df["date"] = pd.to_datetime(
                    df["date"], format="%Y-%m-%d", errors="coerce"
                )
                df[indicator_name] = pd.to_numeric(df[indicator_name], errors="coerce")

                # Drop rows with conversion errors or missing date
                df.dropna(subset=["date", indicator_name], inplace=True)

                if df.empty:
                    logger.warning(
                        f"Data for Vector {req_vector_id} ({indicator_name}) became empty after date/value conversion."
                    )
                    continue

                logger.info(
                    f"Successfully parsed {len(df)} data points for Vector {req_vector_id} ({indicator_name})"
                )
                # Set date as index for easier merging later
                all_vector_dfs.append(df.set_index("date"))

            # Merge all individual vector DataFrames
            if not all_vector_dfs:
                logger.error("Failed to parse data for any requested StatCan vectors.")
                return pd.DataFrame()

            # Start with the first DataFrame and merge others onto it
            master_df = all_vector_dfs[0]
            for i in range(1, len(all_vector_dfs)):
                # Use pd.merge for potentially non-unique index (though date should be unique per vector)
                master_df = pd.merge(
                    master_df,
                    all_vector_dfs[i],
                    left_index=True,
                    right_index=True,
                    how="outer",
                )

            # Reset index to get 'date' back as a column
            master_df = master_df.reset_index()

            # Sort by date after merging
            master_df = master_df.sort_values("date").reset_index(drop=True)
            logger.info(
                f"Final downloaded StatCan data shape after merging vectors: {master_df.shape}"
            )
            return master_df

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching StatCan vector data.")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else "N/A"
            response_text = e.response.text if e.response is not None else "N/A"
            logger.error(
                f"HTTP error fetching StatCan vector data: Status {status_code}, Error: {e}, Response: {response_text[:500]}"
            )
            # Check for JSON syntax error specifically
            if status_code == 406 and "JSON syntax error" in response_text:
                logger.error(
                    "API reported JSON syntax error. Double-check payload structure and headers."
                )
            return pd.DataFrame()
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing StatCan vector response: {e}")
            try:
                # Log the raw response if parsing fails
                logger.error(
                    f"Raw response text (first 500 chars): {response.text[:500]}"
                )
            except NameError:  # response might not exist if request failed
                pass
            except AttributeError:  # response might not have .text
                logger.error(f"Could not get raw response text.")

            return pd.DataFrame()
        except Exception as e:
            logger.error(
                f"Unexpected error fetching StatCan vector data: {e}", exc_info=True
            )
            return pd.DataFrame()

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the Statistics Canada economic indicators data.
        """
        required_cols = ["year", "month", "date_str"]
        # Get indicator names from the keys of the indicators dictionary
        indicator_cols = list(self.indicators.keys())
        expected_cols = required_cols + indicator_cols

        if df.empty:
            logger.warning(
                "Empty DataFrame passed to preprocess for Statistics Canada data"
            )
            return pd.DataFrame(columns=expected_cols).astype(
                {"year": "Int64", "month": "Int64", "date_str": "object"}
            )

        # Ensure 'date' column is datetime
        if "date" not in df.columns or not pd.api.types.is_datetime64_any_dtype(
            df["date"]
        ):
            logger.error(
                "Statistics Canada preprocess requires a 'date' column of datetime type."
            )
            # If no date column, cannot proceed
            return pd.DataFrame(columns=expected_cols).astype(
                {"year": "Int64", "month": "Int64", "date_str": "object"}
            )

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        # Add year and month columns
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        # Create date_str in YYYY-MM format
        df["date_str"] = (
            df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
        )

        # Convert types
        df["year"] = df["year"].astype("Int64")
        df["month"] = df["month"].astype("Int64")

        # Ensure indicator columns are numeric, add missing ones as NaN
        for col in indicator_cols:
            if col in df.columns:
                # Use float64 to accommodate potential NaNs
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
            else:
                # This shouldn't happen if download merged correctly, but handle defensively
                logger.warning(
                    f"Indicator column '{col}' missing in StatCan preprocess. Adding as NaN."
                )
                df[col] = pd.NA  # Use pandas NA

        # Select and order final columns
        final_cols = required_cols + [
            col for col in indicator_cols if col in df.columns
        ]
        # Drop the original 'date' column as it's represented by year/month/date_str
        df = df[final_cols]

        logger.info(
            f"Statistics Canada data preprocessed into {len(df)} monthly records."
        )
        logger.debug(f"Statistics Canada data dtypes:\n{df.dtypes}")
        logger.debug(f"Sample Statistics Canada data:\n{df.head(3)}")

        return df


class CMHCHousingData(EconomicDataSource):
    """CMHC housing data source (Placeholder)."""

    def __init__(self):
        """Initialize the CMHC housing data source."""
        super().__init__("CMHC Housing Data")
        logger.warning(
            "CMHC does not provide a public, easily accessible API for granular housing data (starts, completions)."
        )
        logger.warning(
            "This class is a placeholder. Real data fetching would likely require web scraping or manual data sourcing."
        )

    def download(self) -> pd.DataFrame:
        """
        Download housing data from CMHC (Placeholder).
        """
        logger.info(
            "CMHC data download is not implemented (no public API). Returning empty DataFrame."
        )
        cols = [
            "date",
            "housing_starts_gta",
            "housing_completions_gta",
            "under_construction_gta",
        ]
        return pd.DataFrame(columns=cols)

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the CMHC housing data (Placeholder).
        """
        logger.warning(
            "Preprocessing CMHC data, but input DataFrame is expected to be empty."
        )
        required_cols = ["year", "month", "date_str"]
        indicator_cols = [
            "housing_starts_gta",
            "housing_completions_gta",
            "under_construction_gta",
        ]
        derived_cols = [
            "housing_starts_gta_3m_avg",
            "housing_starts_gta_yoy_change",
            "housing_completions_gta_yoy_change",
            "starts_to_completion_ratio",
        ]

        final_cols = required_cols + indicator_cols + derived_cols
        empty_processed_df = pd.DataFrame(columns=final_cols)

        # Ensure correct dtypes for the empty DataFrame structure
        empty_processed_df["year"] = empty_processed_df["year"].astype("Int64")
        empty_processed_df["month"] = empty_processed_df["month"].astype("Int64")
        for col in indicator_cols + derived_cols:
            empty_processed_df[col] = pd.to_numeric(
                empty_processed_df[col], errors="coerce"
            ).astype("float64")

        logger.info("Returning empty structured DataFrame for CMHC data.")
        return empty_processed_df


# Factory function to get all data sources
def get_all_data_sources() -> List[EconomicDataSource]:
    """
    Get all available economic data sources.
    """
    return [
        BankOfCanadaRates(),
        StatisticsCanadaEconomic(),
        CMHCHousingData(),
    ]


# Example usage (optional, for testing purposes)
if __name__ == "__main__":
    logger.info("--- Testing Economic Data Sources ---")

    if not ECONOMIC_DIR.exists():
        ECONOMIC_DIR.mkdir(parents=True)

    # Certifi install check removed as verify=False is used
    sources = get_all_data_sources()
    all_data = {}

    for source in sources:
        logger.info(f"\n--- Getting data for: {source.name} ---")
        # Set force_download=True initially to ensure download works with verify=False
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

    # Example: Access specific data and check for issues
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
