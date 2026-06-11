"""
Application startup and shutdown hooks.
Initializes mode, data sources, and background services on boot.
"""

import logging
import os

from app.config import settings
from app.core.app_modes import mode_manager
from app.core.data_manager import data_manager
from app.core.mongodb import connect_to_mongo, close_mongo_connection

logger = logging.getLogger(__name__)


async def startup():
    """Run on application startup."""
    logger.info(
        f"🚀 Starting {settings.app_name} v{settings.version} "
        f"in {settings.app_mode.value.upper()} mode"
    )

    # Ensure data directories exist
    os.makedirs(settings.data_upload_path, exist_ok=True)
    os.makedirs(settings.kaggle_data_path, exist_ok=True)
    os.makedirs("./data/samples", exist_ok=True)
    os.makedirs("./data/seed", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

    # Initialize MongoDB client
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.error(f"Could not connect to MongoDB on startup: {e}")

    # Initialize default data source
    try:
        await data_manager.initialize_data_source(settings.data_source)
    except Exception as e:
        logger.warning(f"Could not initialize default data source: {e}")

    logger.info(f"✅ Application started in {mode_manager.current_mode.value} mode")
    logger.info(f"📊 Data source: {mode_manager.data_source.value}")
    logger.info(f"🌐 API available at http://{settings.api_host}:{settings.api_port}")


async def shutdown():
    """Run on application shutdown."""
    logger.info("🛑 Shutting down application...")
    try:
        await close_mongo_connection()
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")
    logger.info("✅ Shutdown complete")
