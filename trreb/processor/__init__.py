"""
Processor package for TRREB data.
"""

from trreb.processor.normalization import (
    standardize_region_names,
    standardize_column_names,
    convert_numeric_columns,
    add_hierarchy_columns,
    add_date_components,
    normalize_dataset,
)
from trreb.processor.validation import (
    ValidationResult,
    validate_regions,
    validate_numeric_columns,
    validate_data_consistency,
    validate_time_series_continuity,
    generate_validation_report,
)

__all__ = [
    # Normalization
    "standardize_region_names",
    "standardize_column_names",
    "convert_numeric_columns",
    "add_hierarchy_columns",
    "add_date_components",
    "normalize_dataset",
    
    # Validation
    "ValidationResult",
    "validate_regions",
    "validate_numeric_columns",
    "validate_data_consistency",
    "validate_time_series_continuity",
    "generate_validation_report",
]
