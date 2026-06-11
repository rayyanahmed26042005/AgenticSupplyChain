"""
Abstract base class for all data ingesters.
Defines the interface that CSV, Kafka, API, Manual, and Kaggle ingesters implement.
"""

from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseIngester(ABC):
    """Abstract base class for all data ingesters."""

    def __init__(self):
        self.name = self.__class__.__name__
        self.last_ingestion_time: str | None = None

    @abstractmethod
    async def ingest(self, source: str) -> Any:
        """
        Ingest data from source.

        Args:
            source: Source identifier (path, URL, config, etc.)

        Returns:
            Ingested data (typically pandas DataFrame)
        """
        pass

    @abstractmethod
    async def validate_source(self, source: str) -> bool:
        """Validate that source is accessible and valid."""
        pass

    async def enrich_data(self, data: Any) -> Any:
        """Optional: Enrich data with calculated fields."""
        return data

    async def transform_data(self, data: Any) -> Any:
        """Optional: Transform data to standard format."""
        return data

    def _mark_ingestion(self):
        """Record ingestion timestamp."""
        self.last_ingestion_time = datetime.now().isoformat()
