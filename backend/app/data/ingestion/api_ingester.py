"""
API Ingester.
Ingest data from REST APIs (supplier APIs, market data, etc.).
"""

from typing import Dict, Any
import logging
import httpx

from app.data.ingestion.base_ingester import BaseIngester

logger = logging.getLogger(__name__)


class APIIngester(BaseIngester):
    """Ingest data from REST APIs."""

    def __init__(self):
        super().__init__()

    async def ingest(self, source: str) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        logger.info(f"Fetching data from API: {source}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(source, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                self._mark_ingestion()
                logger.info(f"✅ Fetched data from API: {source}")
                return data

        except Exception as e:
            logger.error(f"Failed to fetch from API: {e}")
            raise

    async def validate_source(self, source: str) -> bool:
        """Check if API endpoint is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(source, timeout=5.0)
                return response.status_code < 400
        except Exception:
            return False

    async def post_data(self, url: str, payload: Dict) -> Dict[str, Any]:
        """POST data to an API endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
