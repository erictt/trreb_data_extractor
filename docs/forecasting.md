# TRREB Data Forecasting Documentation

## Overview
The TRREB Data Forecasting service provides time series forecasting capabilities for Toronto real estate market data. It supports multiple forecasting models and can predict various market indicators like median prices, sales volumes, and other metrics.

## Features
- Multiple forecasting models (SARIMAX, LightGBM)
- Support for different property types (all_home_types, detached)
- Region-specific forecasting
- Configurable forecast horizon
- Model evaluation and performance metrics
- Result visualization and storage

## Data Prerequisites
- Input data should be preprocessed and normalized using the TRREB Data Extractor pipeline
- Data should include economic indicators (integrated via the economic service)
- Required columns depend on target variable selection
- Data must be chronologically ordered

## Command Line Interface
The forecasting functionality can be accessed through the CLI using:
```bash
python -m trreb.cli forecast [OPTIONS]
```

### CLI Options
- `--input-type`: Type of housing data ("all_home_types" or "detached") [default: all_home_types]
- `--model-type`: Model selection ("sarimax", "lgbm", or "all") [default: all]
- `--target-variable`: Variable to forecast [default: "Median Price"]
- `--forecast-horizon`: Number of months ahead to forecast [default: 6]
- `--region`: Specific region to forecast [default: "TRREB Total"]
- `--output-dir`: Custom directory for results [default: config.FORECAST_DIR]
- `--save-model`: Flag to save trained models
- `--plot`: Flag to generate forecast visualizations

## Models

### SARIMAX (Seasonal ARIMA with Exogenous Variables)
- Handles both seasonal and non-seasonal components
- Incorporates external economic indicators
- Suitable for capturing market cycles and seasonality
- Uses pmdarima for automated model selection

Key parameters:
```python
sarimax_model = train_sarimax(
    y_train=y_train_sarimax,
    exog_train=exog_train_sarimax,
    m=12,  # Monthly seasonality
)
```

### LightGBM
- Gradient boosting framework
- Handles non-linear relationships
- Feature importance analysis
- Suitable for complex patterns and multiple features

Key parameters:
```python
lgbm_model = train_lgbm(
    X_train=X_train,
    y_train=y_train_shifted,
    X_val=X_val,
    y_val=y_val_shifted,
    early_stopping_rounds=50,
)
```

## Data Preparation Pipeline

1. Data Loading
   - Reads processed CSV files from `PROCESSED_DIR`
   - Filters for specified region
   - Validates data completeness

2. Feature Engineering
   - Creates lagged features
   - Adds economic indicators
   - Handles seasonality indicators
   - Scales numerical features

3. Target Preparation
   - Shifts target variable for future prediction
   - Handles missing values
   - Validates target variable quality

4. Train-Validation-Test Split
   - Chronological splitting
   - Preserves time series nature
   - Default splits: 70% train, 15% validation, 15% test

## Output Directory Structure
For each forecast run, the following structure is created:
```
FORECAST_DIR/
└── {input_type}_{target_variable}_{region}_{timestamp}/
    ├── prepared_data.csv
    ├── predictions_sarimax.csv
    ├── predictions_lgbm.csv
    ├── plot_sarimax.png
    ├── plot_lgbm.png
    ├── model_sarimax.joblib
    ├── model_lgbm.joblib
    └── run_summary.json
```

## Model Evaluation
Performance metrics included in run_summary.json:
- Mean Absolute Error (MAE)
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- R-squared (R²)

## Best Practices

### Model Selection
- Use SARIMAX for:
  - Strong seasonal patterns
  - Clear trend components
  - Limited feature set
  - Interpretability needs

- Use LightGBM for:
  - Complex non-linear patterns
  - Large feature sets
  - When feature importance is needed
  - When higher accuracy is priority over interpretability

### Region Selection
- Start with "TRREB Total" for overall market trends
- Consider regional hierarchy for local analysis
- Ensure sufficient data points for chosen region

### Forecast Horizon
- Short-term (1-3 months): Higher accuracy expected
- Medium-term (4-6 months): Reasonable accuracy
- Long-term (>6 months): Increased uncertainty

### Target Variable Selection
- "Median Price": Most stable for price forecasting
- "Sales": More volatile, shorter horizon recommended
- "New Listings": Moderate volatility
- "SNLR Trend": Good for market balance indicators

## Limitations and Considerations
1. Data Quality
   - Missing values impact model performance
   - Recent market changes may not be captured
   - Economic indicator lag effects

2. Model Assumptions
   - SARIMAX assumes linear relationships
   - LightGBM requires sufficient training data
   - Both assume pattern consistency

3. Market Volatility
   - External factors may impact accuracy
   - Policy changes can affect predictions
   - Market shocks may not be predictable

4. Region-Specific
   - Smaller regions may have data sparsity
   - Different regions may require different models
   - Consider regional market dynamics

## Troubleshooting

### Common Issues
1. Installation Problems
   ```bash
   # If numpy/pmdarima compatibility issues:
   pip install numpy==2.2.5
   pip install pmdarima==2.0.4
   ```

2. Data Preparation Errors
   - Check input data completeness
   - Verify region names match config
   - Ensure chronological ordering

3. Model Training Issues
   - Increase training data
   - Check for feature collinearity
   - Validate target variable distribution

### Error Messages
1. "ValueError: numpy.dtype size changed"
   - Reinstall numpy and pmdarima
   - Use compatible versions

2. "Empty DataFrame after processing"
   - Check region filter
   - Verify data availability
   - Validate date ranges

## Future Improvements
1. Additional Models
   - Prophet integration
   - Deep learning models
   - Ensemble methods

2. Feature Engineering
   - Advanced economic indicators
   - Market sentiment analysis
   - Spatial features

3. Visualization
   - Interactive plots
   - Confidence intervals
   - Feature importance plots

4. Model Optimization
   - Automated hyperparameter tuning
   - Cross-validation improvements
   - Model selection automation

## Example Usage

Basic forecast:
```bash
python -m trreb.cli forecast --input-type all_home_types --target-variable "Median Price" --region "TRREB Total"
```

Advanced forecast:
```bash
python -m trreb.cli forecast \
    --input-type detached \
    --model-type all \
    --target-variable "Median Price" \
    --forecast-horizon 12 \
    --region "City of Toronto" \
    --save-model \
    --plot
```

## References
- SARIMAX: pmdarima documentation
- LightGBM: LightGBM documentation
- Time Series Forecasting: Best practices
- TRREB Market Analysis: Methodology