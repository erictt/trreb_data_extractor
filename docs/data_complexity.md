# TRREB Data Complexity

## Overview

This document explains the complexity of the Toronto Regional Real Estate Board (TRREB) data extracted by this project. Understanding these complexities is essential for proper data preprocessing, normalization, and feature engineering when building predictive models.

## Data Source Evolution

The TRREB market reports have undergone several formatting and content changes over time, which introduces complexity in data extraction and harmonization:

### PDF Format Changes

1. **Layout Changes**: 
   - Pre-2020 reports use different table layouts compared to newer reports
   - Font sizes, spacing, and page organization vary across years
   - Some reports contain multi-page tables while others contain single-page tables

2. **Extraction Challenges**:
   - Different extraction methods required based on report date (tabula-py vs. AI-based extraction)
   - Table borders and cell structures vary, affecting extraction accuracy
   - Headers and footers sometimes interfere with table detection

## Data Schema Evolution

### Column Name Variations

Column headers change over time, requiring mapping to standardized names:

| Time Period | Sales Column Name | Price Ratio | Days on Market |
|-------------|-------------------|-------------|----------------|
| Pre-2020 | "Number of Sales" | "Avg. SP / LP" | "Avg. DOM" |
| 2020-2022 | "# of Sales" | "Avg. SP/LP" | "Avg. LDOM" |
| Post-2022 | "Sales" | "Avg. SP/LP" | "Avg. LDOM" |

### Numeric Format Variations

1. **Currency Values**:
   - Dollar signs present or absent depending on report era
   - Comma separators inconsistently applied
   - Decimal precision varies across reports

2. **Percentage Values**:
   - Formatting as "58.5%" in some reports vs. "58.5" (without symbol) in others
   - Decimal precision varies (some reports use whole numbers, others use one decimal place)

3. **Data Type Handling**:
   - Column headers sometimes contain trailing numbers (e.g., "Dollar Volume1")
   - First column often unlabeled or labeled as "nan" instead of "Region"
   - Numeric indicators sometimes stored as text with special characters

## Region Name Variations

### Primary Region Name Changes

The main region name has evolved over time:
- "TREB Total" (pre-2020)
- "TRREB Total" (2020-2022)
- "All TRREB Areas" (post-2022)

### Sub-Region Naming Inconsistencies

Several regions have multiple naming conventions across reports:

| Standard Name | Variations |
|---------------|------------|
| East Gwillimbury | "E. Gwillimbury", "East Gwillimbury", "EGswsiallimbury" (typo) |
| Whitchurch-Stouffville | "Whitchurch-Stouffville", "Stouffville" |
| Bradford West Gwillimbury | "Bradford West Gwillimbury", "Bradford West", "Bradford" |

### Region Hierarchy Considerations

The data contains a hierarchical region structure that must be preserved:
- Top level: TRREB Total/All TRREB Areas
- Regional municipalities: Halton Region, Peel Region, etc.
- Local municipalities: Burlington, Milton, etc.

This hierarchy is important for proper geographic analysis and feature engineering.

## Metric Availability Changes

Not all metrics are available across all time periods:

| Metric | Availability |
|--------|--------------|
| Avg. PDOM | Only in reports after 2020 |
| Median Price | Consistently available across reports |
| SNLR (Trend) | Formatting and naming varies |
| Mos Inv (Trend) | Formatting and naming varies |

## Data Preprocessing Challenges

### Consistency Enforcement

Key challenges when normalizing this data include:

1. **Region Name Standardization**:
   - Mapping variant names to standard forms
   - Handling typos and abbreviations
   - Maintaining region hierarchy information

2. **Column Harmonization**:
   - Creating a unified schema across all time periods
   - Mapping variant column names to standard forms
   - Handling columns that appear or disappear over time

3. **Numeric Value Normalization**:
   - Converting all currency values to consistent format
   - Converting percentage values to decimal form for analysis
   - Ensuring consistent decimal precision

4. **Missing Data Handling**:
   - Identifying truly missing data vs. metrics not collected in that period
   - Appropriate imputation strategies for time series
   - Documentation of data provenance

## Time Series Considerations

When building time series models with this data, special attention must be paid to:

1. **Temporal Consistency**:
   - Ensuring date extraction from filenames is accurate
   - Handling report delays (some reports may cover a month but be released later)
   - Accounting for seasonal patterns in real estate data

2. **Region Tracking**:
   - Ensuring consistent region tracking despite name changes
   - Handling regions that appear or disappear from reports
   - Appropriate aggregation levels for modeling

3. **Metric Interpretation Changes**:
   - Some metrics may have definition changes over time
   - Market context changes (e.g., COVID-19 period vs. pre-pandemic)
   - Regulatory changes affecting market behavior

## Best Practices for Working with This Data

1. **Data Validation**:
   - Always verify region names against a standardized list
   - Check numeric ranges for outliers caused by extraction errors
   - Validate temporal patterns for consistency

2. **Preprocessing Pipeline**:
   - Create a dedicated normalization pipeline that handles all variations
   - Document all transformations applied to the original data
   - Use configuration files to manage region name mappings and schema changes

3. **Feature Engineering**:
   - Create derived features that are robust to changing data definitions
   - Consider ratio-based features that normalize across time periods
   - Include temporal context features (month, season, year, etc.)

4. **Model Development**:
   - Use validation strategies that respect the temporal nature of the data
   - Consider ensemble approaches that handle different data eras separately
   - Incorporate uncertainty estimation to account for data quality variations
