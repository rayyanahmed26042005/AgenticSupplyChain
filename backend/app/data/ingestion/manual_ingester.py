"""
Manual Data Ingester.
Handles manual data entry via API with record validation and buffering.
"""

from typing import Dict, List, Any
import pandas as pd
import logging
from datetime import datetime

from app.data.ingestion.base_ingester import BaseIngester

logger = logging.getLogger(__name__)


class ManualIngester(BaseIngester):
    """Handle manual data entry via API endpoints."""

    def __init__(self):
        super().__init__()
        self.data_buffer: Dict[str, List[Dict]] = {}

    async def ingest(self, source: str = "manual_input") -> pd.DataFrame:
        """Convert buffered records to DataFrame."""
        if source not in self.data_buffer or not self.data_buffer[source]:
            return pd.DataFrame()

        df = pd.DataFrame(self.data_buffer[source])
        df = await self.enrich_data(df)
        self._mark_ingestion()
        logger.info(f"Ingested {len(df)} records from manual input '{source}'")
        return df

    async def validate_source(self, source: str) -> bool:
        """Always true for manual data."""
        return True

    async def load_buffers(self):
        """Load buffers from MongoDB on startup."""
        from app.core.mongodb import mongodb
        if mongodb.db is not None:
            try:
                cursor = mongodb.db["manual_buffers"].find({})
                async for doc in cursor:
                    self.data_buffer[doc["dataset_name"]] = doc["records"]
                logger.info("Loaded manual buffers from MongoDB.")
            except Exception as e:
                logger.error(f"Failed to load manual buffers from MongoDB: {e}")

    async def add_record(self, dataset_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single record to the dataset buffer."""
        if dataset_name not in self.data_buffer:
            self.data_buffer[dataset_name] = []

        # Add metadata
        record.setdefault("id", len(self.data_buffer[dataset_name]) + 1)
        record.setdefault("timestamp", datetime.now().isoformat())
        record.setdefault("type", "manual_entry")

        self.data_buffer[dataset_name].append(record)
        count = len(self.data_buffer[dataset_name])
        logger.info(f"Added record to {dataset_name}: {count} total")

        # Save to MongoDB
        from app.core.mongodb import mongodb
        if mongodb.db is not None:
            try:
                await mongodb.db["manual_buffers"].update_one(
                    {"dataset_name": dataset_name},
                    {"$set": {"dataset_name": dataset_name, "records": self.data_buffer[dataset_name]}},
                    upsert=True
                )
                logger.info(f"Saved manual buffer for '{dataset_name}' to MongoDB.")
            except Exception as e:
                logger.error(f"Failed to save manual buffer to MongoDB: {e}")

        return {"dataset": dataset_name, "record_count": count}

    async def add_batch(
        self, dataset_name: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add multiple records at once."""
        if dataset_name not in self.data_buffer:
            self.data_buffer[dataset_name] = []

        for record in records:
            record.setdefault("id", len(self.data_buffer[dataset_name]) + 1)
            record.setdefault("timestamp", datetime.now().isoformat())
            record.setdefault("type", "manual_entry")
            self.data_buffer[dataset_name].append(record)

        count = len(self.data_buffer[dataset_name])
        logger.info(f"Added {len(records)} records to {dataset_name}")

        # Save to MongoDB
        from app.core.mongodb import mongodb
        if mongodb.db is not None:
            try:
                await mongodb.db["manual_buffers"].update_one(
                    {"dataset_name": dataset_name},
                    {"$set": {"dataset_name": dataset_name, "records": self.data_buffer[dataset_name]}},
                    upsert=True
                )
                logger.info(f"Saved manual buffer batch for '{dataset_name}' to MongoDB.")
            except Exception as e:
                logger.error(f"Failed to save manual buffer batch to MongoDB: {e}")

        return {"dataset": dataset_name, "added": len(records), "total": count}

    def get_dataset_stats(self, dataset_name: str) -> Dict[str, Any]:
        """Get stats about a buffered dataset."""
        if dataset_name not in self.data_buffer:
            return {"name": dataset_name, "record_count": 0, "columns": []}

        records = self.data_buffer[dataset_name]
        return {
            "name": dataset_name,
            "record_count": len(records),
            "columns": list(records[0].keys()) if records else [],
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get stats for all buffered datasets."""
        return {
            name: self.get_dataset_stats(name)
            for name in self.data_buffer
        }

    def clear_buffer(self, dataset_name: str = None):
        """Clear data buffer for a dataset or all datasets."""
        if dataset_name:
            self.data_buffer.pop(dataset_name, None)
        else:
            self.data_buffer.clear()

    async def enrich_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Enrich manually entered data."""
        if "timestamp" not in data.columns:
            data["timestamp"] = pd.Timestamp.now()
        data["manual_entry"] = True
        data["validated"] = True
        return data
