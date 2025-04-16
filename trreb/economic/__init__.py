"""
Economic data integration package for TRREB data.
"""

from trreb.economic.sources import (
    EconomicDataSource,
    BankOfCanadaRates,
    StatisticsCanadaEconomic,
    CMHCHousingData,
    get_all_data_sources,
)
from trreb.economic.integration import (
    load_economic_data,
    create_master_economic_dataset,
    enrich_trreb_data,
    enrich_all_datasets,
)

__all__ = [
    # Data sources
    "EconomicDataSource",
    "BankOfCanadaRates",
    "StatisticsCanadaEconomic",
    "CMHCHousingData",
    "get_all_data_sources",
    
    # Integration
    "load_economic_data",
    "create_master_economic_dataset",
    "enrich_trreb_data",
    "enrich_all_datasets",
]
