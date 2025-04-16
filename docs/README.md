# TRREB Data Extractor Documentation

This directory contains documentation for the TRREB Data Extractor project, which aims to process Toronto Regional Real Estate Board market reports into structured data for machine learning-based housing price prediction in the Greater Toronto Area (GTA).

## Contents

- **[data_complexity.md](./data_complexity.md)**: Detailed explanation of the challenges and complexities in the TRREB data, including changes in format, region naming, and data structure over time.

- **[general_prompt.md](./general_prompt.md)**: A comprehensive prompt template for assigning tasks to developers or AI agents working on this project. This provides context about the project's goals, structure, and technical requirements.

- **[economic_indicators.md](./economic_indicators.md)**: Comprehensive guide to relevant economic indicators (interest rates, employment metrics, inflation, population trends, etc.) that can be integrated with the TRREB data to enhance housing price prediction models.

## Project End Goal

The ultimate goal of this project is to build a robust machine learning model that can accurately predict housing prices across different regions in the GTA, Ontario. The project follows this progression:

1. **Data Extraction & Processing**: Extract and normalize historical real estate data from TRREB reports (2016-present).

2. **Data Enrichment**: Integrate economic indicators and other external factors that influence housing prices.

3. **Feature Engineering**: Create derived features that capture market dynamics, seasonality, region-specific characteristics, and macroeconomic effects.

4. **Model Development**: Train and validate various machine learning models that can predict:
   - Short-term price movements (1-3 months ahead)
   - Medium-term price trends (3-12 months ahead)
   - Regional price differences and growth rates
   - Property-type specific forecasts (detached homes, etc.)

5. **Model Deployment**: Create a usable prediction tool that can be updated with new data and provide ongoing forecasts.

## Using This Documentation

### For New Developers

Start by reading the general_prompt.md to understand the project's overall structure and goals. Then review data_complexity.md to understand the specific challenges you'll need to address when working with the TRREB data. If you're working on model development, also review economic_indicators.md for context on additional data sources.

### For Task Assignment

When assigning tasks to AI assistants or other developers, use the general_prompt.md as a template and add specific details about the task you need completed. The prompt provides comprehensive background that helps anyone understand the project context without extensive onboarding.

### For Data Processing

Before implementing data normalization or feature engineering for machine learning, review data_complexity.md to understand the specific variations and challenges in the dataset that your code will need to handle.

### For Model Development

When working on the machine learning aspects of the project, leverage the information in economic_indicators.md to incorporate relevant economic factors that influence housing prices, enhancing model accuracy and explanatory power.

## Documentation Updates

This documentation should be updated when:
- New data formats or variations are encountered
- The project structure or goals change significantly
- New best practices for handling the data are identified
- New data sources or economic indicators are integrated
- Model architecture or feature engineering approaches change
