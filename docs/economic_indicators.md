# Economic Indicators for Housing Price Prediction

## Overview

This document outlines the economic indicators that can be integrated with the TRREB real estate data to improve the accuracy and contextual awareness of housing price prediction models. Economic factors have significant influence on real estate markets and provide valuable macroeconomic context that complements transaction-level data.

## Recommended Economic Indicators

### 1. Interest Rates

Interest rates directly impact borrowing costs and housing affordability, making them crucial predictors for housing market activity.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Bank of Canada Overnight Rate | The primary interest rate set by the central bank | Monthly | Directly affects variable mortgage rates |
| 5-Year Fixed Mortgage Rates | The most common mortgage term in Canada | Weekly/Monthly | Direct impact on housing affordability |
| Variable Mortgage Rates | Rates that fluctuate with the prime rate | Weekly/Monthly | Growing segment of the mortgage market |
| Prime Rate | The base rate banks use to set interest rates for loans | Monthly | Reference point for variable mortgages |

**Source**: Bank of Canada, Statistics Canada (CANSIM tables), major Canadian banks, financial data providers like Bloomberg

### 2. Employment Metrics

Employment stability and growth strongly correlate with housing demand and price sustainability.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Ontario Unemployment Rate | Percentage of working population without jobs | Monthly | Provincial economic health indicator |
| GTA Unemployment Rate | Metropolitan area specific unemployment | Monthly | Local economic conditions |
| Employment Growth Rate | Change in employed persons over time | Monthly | Economic momentum indicator |
| Sector-Specific Employment | Jobs in construction, real estate, finance | Monthly | Industry-specific impacts on housing |

**Source**: Statistics Canada Labour Force Survey, CANSIM tables

### 3. Inflation and Consumer Price Indices

Inflation affects purchasing power and investment decisions, including real estate.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Consumer Price Index (CPI) | Measures changes in price level of consumer goods | Monthly | General inflation measure |
| Core Inflation Rate | CPI excluding volatile items like food and energy | Monthly | Underlying inflation trends |
| Housing Component of CPI | Housing-specific inflation measure | Monthly | Direct measure of housing cost increases |
| New Housing Price Index | Price changes for new residential buildings | Monthly | Construction cost and new home pricing indicator |

**Source**: Statistics Canada, Bank of Canada

### 4. Population and Migration

Population dynamics drive long-term housing demand.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Net Migration to GTA/Ontario | Incoming minus outgoing population | Quarterly | Direct driver of housing demand |
| Population Growth Rate | Percentage change in population | Annual | Long-term demand predictor |
| Immigration Levels | Number of new permanent residents | Monthly/Quarterly | Major component of GTA population growth |
| Interprovincial Migration | Movement between Canadian provinces | Quarterly | Domestic population shifts |

**Source**: Statistics Canada, Immigration, Refugees and Citizenship Canada (IRCC)

### 5. Construction and Housing Supply

Supply-side indicators help predict market balance and price pressures.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Housing Starts | New residential construction projects | Monthly | Future housing supply indicator |
| Building Permits Issued | Authorized construction projects | Monthly | Leading indicator for construction |
| Completion Rates | Finished housing units | Monthly | Actual new supply entering the market |
| Units Under Construction | Current building activity | Monthly | Pipeline of upcoming inventory |

**Source**: Canada Mortgage and Housing Corporation (CMHC), municipal data

### 6. Income and Affordability

Income levels constrain how much buyers can afford to pay for housing.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Median Household Income | Middle income value for households | Annual | Purchasing power indicator |
| Housing Affordability Index | Ratio of housing costs to income | Quarterly | Sustainability measure for prices |
| Debt-to-Income Ratios | Total debt relative to annual income | Quarterly | Financial health of potential buyers |
| Disposable Income Growth | After-tax income change | Quarterly | Available funds for housing |

**Source**: Statistics Canada, CMHC

### 7. Real Estate Investment

Investment activity provides insight into market confidence and external pressures.

| Indicator | Description | Frequency | Relevance |
|-----------|-------------|-----------|-----------|
| Foreign Investment | Non-resident purchase of residential properties | Quarterly | External market influence |
| REIT Performance | Real Estate Investment Trust metrics | Monthly | Institutional real estate sentiment |
| Residential Investment | GDP component measuring investment in housing | Quarterly | Economic resource allocation to housing |

**Source**: Canadian Real Estate Association, local real estate boards, Statistics Canada

## Data Sources

### Primary Sources

1. **Statistics Canada** (https://www.statcan.gc.ca)
   - Access via API: https://www.statcan.gc.ca/en/developers/wds
   - CANSIM tables (now called "Tables"): https://www150.statcan.gc.ca/n1/en/type/data
   - Many datasets available for free download

2. **Bank of Canada** (https://www.bankofcanada.ca)
   - Interest rate data: https://www.bankofcanada.ca/rates/
   - Downloadable as CSV or accessible via API
   - Historical statistics tool for long-term trends

3. **Canada Mortgage and Housing Corporation (CMHC)** (https://www.cmhc-schl.gc.ca)
   - Housing Market Information Portal: https://www.cmhc-schl.gc.ca/hmiportal
   - Housing starts, completions, and market assessments
   - Housing market outlook reports

4. **Ontario Ministry of Finance** (https://www.ontario.ca/page/ministry-finance)
   - Provincial economic indicators and forecasts
   - Ontario Economic Accounts

5. **Toronto Open Data Portal** (https://open.toronto.ca)
   - Local demographic and economic data
   - Building permits and development applications

### Additional Resources

6. **Federal Reserve Economic Data (FRED)** (https://fred.stlouisfed.org)
   - Comprehensive economic database
   - Canadian indicators from various primary sources
   - Excellent API for programmatic access

7. **Canadian Real Estate Association (CREA)** (https://www.crea.ca)
   - National housing statistics
   - MLS® Home Price Index methodology

8. **Toronto Regional Real Estate Board (TRREB)** (https://trreb.ca)
   - Market Watch reports (already used in this project)
   - Additional market analysis beyond the PDF reports

## Implementation Considerations

### 1. Data Frequency Alignment

Many economic indicators are published monthly, which aligns well with the TRREB data. However, some important metrics (like income data) may only be available quarterly or annually. Consider:

- Interpolation techniques for lower-frequency data
- Using the most recent available data point for each month
- Creating features that represent "time since last change" for rarely updated indicators

### 2. Temporal Relationships

Economic changes typically affect housing markets with a lag. Consider creating features with various time shifts:

- Concurrent values (same month)
- Lagged values (1-12 months prior)
- Moving averages (3, 6, 12-month rolling windows)
- Year-over-year change rates

### 3. Geographic Granularity

Match economic indicators to the appropriate geographic level when possible:

| Level | Examples |
|-------|----------|
| National | Bank of Canada rate, immigration levels |
| Provincial | Ontario unemployment rate, provincial GDP |
| Regional | GTA-specific metrics, regional employment |
| Municipal | City-level building permits, local population |

### 4. Feature Engineering Ideas

Create derived features that capture economic relationships:

- Price-to-income ratios by region
- Mortgage payment affordability index (using interest rates and income)
- Supply-demand balance indicators
- Housing investment as percentage of GDP
- Spread between fixed and variable mortgage rates

### 5. Data Pipeline Integration

Incorporate economic data collection into the existing pipeline:

1. Create a separate module for economic data acquisition
2. Implement scheduled updates for indicators (many are released on fixed schedules)
3. Build a unified dataset that joins TRREB data with economic indicators on date/time keys
4. Document the provenance and update frequency of each indicator

## Model Enhancement Strategy

When integrating economic indicators with the TRREB data for modeling:

1. **Baseline Comparison**: Establish a baseline model using only TRREB data, then measure improvement when adding economic factors

2. **Feature Importance Analysis**: Determine which economic indicators provide the most predictive power

3. **Regional Sensitivity**: Analyze how different regions respond to economic changes (some may be more sensitive to interest rates, others to employment)

4. **Scenario Testing**: Use economic indicators to simulate market scenarios (rising rates, economic downturn, population surge)

5. **Multivariate Time Series Modeling**: Explore models that specifically handle complex temporal relationships between economic factors and housing prices
