"""
Integration of economic data with TRREB real estate data.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from trreb.config import PROCESSED_DIR, ECONOMIC_DIR
from trreb.economic.sources import get_all_data_sources
from trreb.utils.logging import logger


def load_economic_data(force_download: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Load all economic data sources.
    
    Args:
        force_download: Whether to force download even if cached data is available
        
    Returns:
        Dictionary of data source name to DataFrame
    """
    data_sources = get_all_data_sources()
    economic_data = {}
    
    for source in data_sources:
        try:
            df = source.get_data(force_download=force_download)
            if df is not None and not df.empty:
                economic_data[source.name] = df
                logger.info(f"Loaded {len(df)} rows from {source.name}")
            else:
                logger.warning(f"No data loaded from {source.name}")
        except Exception as e:
            logger.error(f"Error loading data from {source.name}: {e}")
    
    return economic_data


def create_master_economic_dataset() -> pd.DataFrame:
    """
    Create a master dataset of all economic indicators.
    
    Returns:
        DataFrame containing all economic indicators
    """
    # Load all economic data
    economic_data = load_economic_data()
    
    if not economic_data:
        logger.error("No economic data sources loaded")
        return pd.DataFrame()
    
    # Start with the first data source
    master_df = next(iter(economic_data.values())).copy()
    
    # Merge with other data sources
    for name, df in economic_data.items():
        if df is master_df:
            continue
        
        # Check if 'date_str' column exists
        if 'date_str' not in df.columns:
            logger.warning(f"'date_str' column not found in {name}, skipping")
            continue
        
        # Merge on 'date_str'
        master_df = pd.merge(master_df, df, on='date_str', how='outer', suffixes=('', f'_{name}'))
    
    # Sort by date
    if 'date_str' in master_df.columns:
        master_df = master_df.sort_values('date_str')
    
    # Save the master dataset
    output_path = ECONOMIC_DIR / 'master_economic_data.csv'
    master_df.to_csv(output_path, index=False)
    logger.info(f"Master economic dataset saved to {output_path}")
    
    return master_df


def enrich_trreb_data(property_type: str, include_lags: bool = True, lag_periods: List[int] = [1, 3, 6, 12]) -> pd.DataFrame:
    """
    Enrich TRREB data with economic indicators.
    
    Args:
        property_type: Type of property (all_home_types or detached)
        include_lags: Whether to include lagged economic indicators
        lag_periods: List of lag periods to include
        
    Returns:
        DataFrame containing enriched TRREB data
    """
    # Load normalized TRREB data
    trreb_path = PROCESSED_DIR / f"normalized_{property_type}.csv"
    if not trreb_path.exists():
        logger.error(f"Normalized TRREB data not found at {trreb_path}")
        return pd.DataFrame()
    
    try:
        trreb_df = pd.read_csv(trreb_path)
        
        # Ensure date is in YYYY-MM format
        if 'date' in trreb_df.columns:
            # If date is in datetime format, convert to YYYY-MM string
            if pd.api.types.is_datetime64_dtype(trreb_df['date']):
                trreb_df['date_str'] = trreb_df['date'].dt.strftime('%Y-%m')
            else:
                # Try to parse as date and convert to YYYY-MM
                try:
                    trreb_df['date_str'] = pd.to_datetime(trreb_df['date']).dt.strftime('%Y-%m')
                except:
                    # If parsing fails, use as is if it looks like YYYY-MM
                    if trreb_df['date'].str.match(r'^\d{4}-\d{2}$').all():
                        trreb_df['date_str'] = trreb_df['date']
                    else:
                        logger.error(f"Could not convert 'date' column to YYYY-MM format")
                        return pd.DataFrame()
        else:
            logger.error(f"'date' column not found in TRREB data")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading TRREB data: {e}")
        return pd.DataFrame()
    
    # Load or create master economic dataset
    econ_path = ECONOMIC_DIR / 'master_economic_data.csv'
    if econ_path.exists():
        try:
            econ_df = pd.read_csv(econ_path)
        except Exception as e:
            logger.error(f"Error loading master economic data: {e}")
            econ_df = create_master_economic_dataset()
    else:
        econ_df = create_master_economic_dataset()
    
    if econ_df.empty:
        logger.error("No economic data available")
        return trreb_df
    
    # Create lag features if requested
    if include_lags:
        # Identify numeric columns to lag
        numeric_cols = econ_df.select_dtypes(include=['number']).columns
        
        # For each lag period, create lagged features
        for lag in lag_periods:
            # Create a copy of the economic data shifted by the lag period
            lag_df = econ_df.copy()
            
            # Sort by date_str to ensure correct lagging
            lag_df = lag_df.sort_values('date_str')
            
            # For each numeric column, create a lagged version
            for col in numeric_cols:
                if col in lag_df.columns and col != 'date_str':
                    # Create the lagged feature name
                    lag_col = f"{col}_lag{lag}"
                    
                    # Get the index position of the date_str column
                    try:
                        date_idx = lag_df.columns.get_loc('date_str')
                        
                        # Create a new DataFrame with just the date_str and lagged column
                        temp_df = pd.DataFrame({
                            'date_str': lag_df['date_str'],
                            lag_col: lag_df[col].shift(lag)
                        })
                        
                        # Merge back into the economic data
                        econ_df = pd.merge(econ_df, temp_df, on='date_str', how='left')
                    except Exception as e:
                        logger.error(f"Error creating lag feature {lag_col}: {e}")
    
    # Merge TRREB data with economic data
    enriched_df = pd.merge(trreb_df, econ_df, on='date_str', how='left', suffixes=('', '_econ'))
    
    # Filter out duplicate columns
    cols_to_keep = [col for col in enriched_df.columns if not (col.endswith('_econ') and col.replace('_econ', '') in enriched_df.columns)]
    enriched_df = enriched_df[cols_to_keep]
    
    # Save the enriched dataset
    output_path = PROCESSED_DIR / f"enriched_{property_type}.csv"
    enriched_df.to_csv(output_path, index=False)
    logger.info(f"Enriched TRREB data saved to {output_path}")
    
    return enriched_df


def enrich_all_datasets(include_lags: bool = True, lag_periods: List[int] = [1, 3, 6, 12]) -> Dict[str, pd.DataFrame]:
    """
    Enrich all TRREB datasets with economic indicators.
    
    Args:
        include_lags: Whether to include lagged economic indicators
        lag_periods: List of lag periods to include
        
    Returns:
        Dictionary of property type to enriched DataFrame
    """
    property_types = ["all_home_types", "detached"]
    enriched_data = {}
    
    for property_type in property_types:
        try:
            df = enrich_trreb_data(property_type, include_lags, lag_periods)
            if not df.empty:
                enriched_data[property_type] = df
                logger.info(f"Enriched {property_type} dataset with {len(df)} rows")
            else:
                logger.warning(f"No enriched data created for {property_type}")
        except Exception as e:
            logger.error(f"Error enriching {property_type} data: {e}")
    
    return enriched_data
