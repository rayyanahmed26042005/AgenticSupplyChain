"""
MongoDB connection setup using Motor async driver.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None


mongodb = MongoDB()


async def connect_to_mongo():
    """Establish async MongoDB client connection."""
    uri = settings.mongodb_uri
    try:
        logger.info("Connecting to MongoDB Atlas...")
        mongodb.client = AsyncIOMotorClient(uri)
        mongodb.db = mongodb.client["supply_chain_db"]
        # Ping the server to verify connection
        await mongodb.client.admin.command("ping")
        logger.info("✅ Connected to MongoDB Atlas successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
        mongodb.client = None
        mongodb.db = None
        raise e


async def close_mongo_connection():
    """Close MongoDB client connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("✅ Closed MongoDB connection.")
