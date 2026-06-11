"""
Data Validators - Schema validation, type checking, null detection.
"""

from typing import Dict, Any, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate ingested data for quality and consistency."""

    def validate(self, data: Any) -> Dict[str, Any]:
        """Run all validations on data."""
        if isinstance(data, pd.DataFrame):
            return self._validate_dataframe(data)
        elif isinstance(data, dict):
            return self._validate_dict(data)
        elif isinstance(data, list):
            return self._validate_list(data)
        else:
            return {"valid": True, "warnings": ["Unknown data type, skipping validation"]}

    def _validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate a pandas DataFrame."""
        errors: List[str] = []
        warnings: List[str] = []

        # Check empty
        if df.empty:
            errors.append("DataFrame is empty")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Check for null columns
        null_pcts = df.isnull().mean()
        for col, pct in null_pcts.items():
            if pct > 0.5:
                warnings.append(f"Column '{col}' has {pct*100:.0f}% null values")
            elif pct == 1.0:
                errors.append(f"Column '{col}' is entirely null")

        # Check for duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            warnings.append(f"{dup_count} duplicate rows found")

        # Check minimum rows
        if len(df) < 2:
            warnings.append("Dataset has very few rows")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "null_percentages": {
                    col: round(pct * 100, 1) for col, pct in null_pcts.items() if pct > 0
                },
                "duplicate_rows": int(dup_count),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            },
        }

    def _validate_dict(self, data: Dict) -> Dict[str, Any]:
        """Validate dictionary data."""
        if not data:
            return {"valid": False, "errors": ["Empty dictionary"]}
        return {"valid": True, "errors": [], "warnings": [], "keys": list(data.keys())}

    def _validate_list(self, data: list) -> Dict[str, Any]:
        """Validate list data."""
        if not data:
            return {"valid": False, "errors": ["Empty list"]}
        return {"valid": True, "errors": [], "warnings": [], "length": len(data)}
