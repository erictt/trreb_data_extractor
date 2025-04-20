"""
Economic data integration package for TRREB data.
"""

from trreb.services.economic.sources import (
    EconomicDataSource,
    BankOfCanadaRates,
    StatisticsCanadaEconomic,
    CMHCHousingData,
    get_all_data_sources,
)
from trreb.services.economic.integration import (
    load_economic_data,
    create_master_economic_dataset,
    integrate_economic_data,
    integrate_economic_data_all,
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
    "integrate_economic_data",
    "integrate_economic_data_all",
]
