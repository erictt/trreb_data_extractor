# Economic Indicators for Housing Price Prediction

## Overview

This document outlines the economic indicators currently integrated with the TRREB real estate data via the provided Python code (`sources.py`). These indicators aim to improve the accuracy and contextual awareness of housing price prediction models by providing relevant macroeconomic context.

## Implemented Economic Indicators

### 1. Interest Rates (Source: Bank of Canada VALET API)

Interest rates directly impact borrowing costs and housing affordability.

| Indicator           | Description                                  | Series ID | Frequency                  | Relevance                                     |
| :------------------ | :------------------------------------------- | :-------- | :------------------------- | :-------------------------------------------- |
| `overnight_rate`    | Bank of Canada Target for the Overnight Rate | V122514   | Daily (Aggregated Monthly) | Directly affects variable mortgage rates      |
| `prime_rate`        | Prime Business Loan Rate                     | V80691311 | Monthly                    | Reference point for variable mortgages        |
| `mortgage_5yr_rate` | 5-Year Conventional Mortgage Rate            | V122521   | Monthly                    | Common mortgage term, direct affordability impact |

### 2. Employment Metrics (Source: Statistics Canada WDS API - Vector IDs)

Employment stability and growth strongly correlate with housing demand.

| Indicator                   | Description                                                  | Vector ID | Frequency | Relevance                            |
| :-------------------------- | :----------------------------------------------------------- | :-------- | :-------- | :----------------------------------- |
| `unemployment_rate_ontario` | Ontario Unemployment Rate (Seasonally Adjusted, 15+ years) | v2062815  | Monthly   | Provincial economic health indicator |
| `unemployment_rate_toronto` | Toronto CMA Unemployment Rate (Seasonally Adjusted, 15+ years) | v2062856  | Monthly   | Local economic conditions            |

### 3. Inflation and Consumer Price Indices (Source: Statistics Canada WDS API - Vector IDs)

Inflation affects purchasing power and investment decisions.

| Indicator               | Description                                                        | Vector ID  | Frequency | Relevance                                    |
| :---------------------- | :----------------------------------------------------------------- | :--------- | :-------- | :------------------------------------------- |
| `cpi_all_items_ontario` | Ontario Consumer Price Index (CPI), All Items                      | v41690974  | Monthly   | General inflation measure for the province   |
| `cpi_shelter_ontario`   | Ontario Consumer Price Index (CPI), Shelter Component              | v41691006  | Monthly   | Direct measure of housing cost inflation     |
| `nhpi_toronto`          | Toronto CMA New Housing Price Index (NHPI), Total (House and Land) | v111955442 | Monthly   | New home pricing indicator for the region    |

## Data Sources Implemented

1.  **Bank of Canada** (<https://www.bankofcanada.ca>)
    * Accessed via: VALET API (<https://www.bankofcanada.ca/valet/>)
    * Provides: Interest rate data.

2.  **Statistics Canada** (<https://www.statcan.gc.ca>)
    * Accessed via: Web Data Service (WDS) API using Vector IDs (<https://www.statcan.gc.ca/en/developers/wds>)
    * Provides: Unemployment rates, CPI, NHPI.

## Implementation Notes (Based on `sources.py`)

* **Frequency:** All implemented indicators are fetched or aggregated to a **monthly** frequency.
* **Lagging:** The `integration.py` script includes functionality to create lagged features (e.g., 1, 3, 6, 12 months prior) for these economic indicators.
* **Geographic Scope:** Indicators are specific to Ontario or the Toronto CMA as indicated by their names and source Vector/Series IDs.
* **Data Joining:** Data is joined based on a `YYYY-MM` formatted `date_str` column created during preprocessing.
* **SSL Verification:** Note that the current version of `sources.py` has SSL verification disabled (`verify=False`) as a temporary workaround for environment issues. This is insecure and should be rectified by fixing the underlying system certificate problem.

