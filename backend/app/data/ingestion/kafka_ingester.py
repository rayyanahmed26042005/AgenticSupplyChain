"""
Kafka Ingester (Stub for MVP).
Real-time data ingestion from Kafka — activates when a Kafka broker is available.
For MVP, provides simulated streaming via async generators.
"""

from typing import Dict, Any, List
import logging
import asyncio
import json
from datetime import datetime

from app.data.ingestion.base_ingester import BaseIngester

logger = logging.getLogger(__name__)


class KafkaIngester(BaseIngester):
    """
    Real-time data ingestion from Kafka.
    Used in REALTIME and HYBRID modes.
    Falls back to simulated streaming when no broker is available.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        super().__init__()
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None
        self.running = False
        self.message_buffer: List[Dict] = []
        self.buffer_size = 100
        self._simulated = True  # True when no real Kafka

    async def ingest(self, source: str) -> Dict[str, Any]:
        """
        Start consuming from Kafka topic.
        Falls back to simulated mode if Kafka is unavailable.
        """
        logger.info(f"Attempting Kafka connection for topic: {source}")

        try:
            from kafka import KafkaConsumer

            self.consumer = KafkaConsumer(
                source,
                bootstrap_servers=self.bootstrap_servers.split(","),
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                auto_offset_reset="earliest",
                group_id="supply-chain-group",
            )
            self.running = True
            self._simulated = False
            logger.info(f"✅ Connected to Kafka topic: {source}")
            return {"status": "connected", "topic": source, "simulated": False}

        except Exception as e:
            logger.warning(f"Kafka unavailable ({e}), using simulated mode")
            self._simulated = True
            self.running = True
            return {"status": "simulated", "topic": source, "simulated": True}

    async def validate_source(self, source: str) -> bool:
        """Check if Kafka topic is accessible."""
        try:
            from kafka import KafkaConsumer

            consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers.split(","),
                request_timeout_ms=5000,
            )
            topics = consumer.topics()
            consumer.close()
            return source in topics
        except Exception:
            return False

    async def consume_messages(self, count: int = 10) -> List[Dict]:
        """Consume messages (real or simulated)."""
        if self._simulated:
            return await self._generate_simulated_messages(count)

        messages = []
        if not self.consumer:
            return messages

        try:
            msg = self.consumer.poll(timeout_ms=2000)
            if msg:
                for _, records in msg.items():
                    for record in records:
                        messages.append(record.value)
        except Exception as e:
            logger.error(f"Error consuming: {e}")

        return messages

    async def _generate_simulated_messages(self, count: int) -> List[Dict]:
        """Generate simulated streaming messages for demo."""
        import random

        messages = []
        for _ in range(count):
            msg = {
                "timestamp": datetime.now().isoformat(),
                "type": random.choice(["order", "shipment", "inventory_update"]),
                "product_id": f"PROD-{random.randint(1000, 9999)}",
                "quantity": random.randint(10, 500),
                "status": random.choice(["pending", "in_transit", "delivered"]),
                "supplier_id": f"SUP-{random.randint(100, 999)}",
            }
            messages.append(msg)
            self.message_buffer.append(msg)

        # Trim buffer
        if len(self.message_buffer) > self.buffer_size:
            self.message_buffer = self.message_buffer[-self.buffer_size :]

        return messages

    def stop(self):
        """Stop Kafka consumer."""
        if self.consumer:
            self.consumer.close()
        self.running = False
        logger.info("Kafka consumer stopped")
