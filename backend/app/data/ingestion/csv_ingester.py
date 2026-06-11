"""
CSV Ingester and Kaggle Data Loader.
Handles CSV file uploads and pre-downloaded Kaggle datasets.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, Any
import logging

from app.data.ingestion.base_ingester import BaseIngester
from app.config import settings

logger = logging.getLogger(__name__)


class CSVIngester(BaseIngester):
    """Handle CSV file uploads and ingestion."""

    async def ingest(self, source: str) -> pd.DataFrame:
        """Load CSV file from disk."""
        if not await self.validate_source(source):
            raise ValueError(f"Invalid CSV source: {source}")

        logger.info(f"Loading CSV from: {source}")
        df = pd.read_csv(source)

        df = await self.enrich_data(df)
        df = await self.transform_data(df)
        self._mark_ingestion()

        logger.info(f"Loaded {len(df)} rows from CSV")
        return df

    async def validate_source(self, source: str) -> bool:
        """Validate CSV file exists and is readable."""
        if not os.path.exists(source):
            logger.error(f"CSV file not found: {source}")
            return False

        if not source.lower().endswith(".csv"):
            logger.error(f"File is not CSV: {source}")
            return False

        try:
            pd.read_csv(source, nrows=1)
            return True
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return False

    async def enrich_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Enrich CSV data with calculated fields."""
        # Standardize column names
        data.columns = data.columns.str.lower().str.replace(" ", "_")

        # Calculate common supply chain metrics if columns exist
        if "stock_levels" in data.columns and "products_sold" in data.columns:
            data["inventory_turnover"] = data["products_sold"] / data[
                "stock_levels"
            ].replace(0, 1)

        if "price" in data.columns and "cost" in data.columns:
            data["margin_pct"] = (
                (data["price"] - data["cost"]) / data["price"]
            ) * 100

        return data


class KaggleDataLoader(BaseIngester):
    """Load pre-downloaded Kaggle supply chain datasets."""

    def __init__(self, data_path: str = "./data/kaggle"):
        super().__init__()
        self.data_path = Path(data_path)
        self.expected_files = {
            "supply_chain": "supply_chain.csv",
            "suppliers": "suppliers.csv",
            "products": "products.csv",
            "shipping": "shipping.csv",
            "manufacturing": "manufacturing.csv",
        }

    async def ingest(self, source: str = "all") -> Dict[str, pd.DataFrame]:
        """Load Kaggle datasets. source='all' loads everything available."""
        datasets = {}

        if source == "all":
            files_to_load = self.expected_files
        else:
            filename = self.expected_files.get(source, f"{source}.csv")
            files_to_load = {source: filename}

        for dataset_name, filename in files_to_load.items():
            filepath = self.data_path / filename
            if filepath.exists():
                logger.info(f"Loading {dataset_name} from {filepath}")
                data = pd.read_csv(filepath)
                data = await self.enrich_data(data)
                datasets[dataset_name] = data
            else:
                logger.warning(f"Kaggle file not found: {filepath}")

        self._mark_ingestion()
        logger.info(f"Loaded {len(datasets)} Kaggle datasets")
        return datasets

    async def validate_source(self, source: str) -> bool:
        """Check if Kaggle data directory exists and has files."""
        if not self.data_path.exists():
            return False
        csv_files = list(self.data_path.glob("*.csv"))
        return len(csv_files) > 0

    async def enrich_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Enrich Kaggle data with additional calculated fields."""
        data.columns = data.columns.str.lower().str.replace(" ", "_")

        # Quality score from defect rate
        if "defect_rate" in data.columns:
            data["quality_score"] = 1.0 - (data["defect_rate"] / 100.0).clip(0, 1)

        # Lead time risk categorization
        if "lead_time" in data.columns:
            data["lead_time_risk"] = pd.cut(
                data["lead_time"],
                bins=[0, 7, 15, 30, float("inf")],
                labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            )

        return data

    def get_available_datasets(self) -> Dict[str, bool]:
        """Check which datasets are available on disk."""
        return {
            name: (self.data_path / filename).exists()
            for name, filename in self.expected_files.items()
        }
