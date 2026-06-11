"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.core.startup import startup, shutdown
from app.api.routes import api_router
from app.api.middleware.logging import LoggingMiddleware
from app.events.event_bus import event_bus
from app.events.handlers import register_default_handlers
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    register_default_handlers(event_bus)
    await startup()
    yield
    # Shutdown
    await shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "AI-powered supply chain orchestration platform with autonomous agents, "
            "simulation engine, ML forecasting, and real-time monitoring."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware
    app.add_middleware(LoggingMiddleware)

    # API routes
    app.include_router(api_router, prefix=settings.api_prefix)

    # Root
    @app.get("/")
    async def root():
        return {
            "app": settings.app_name,
            "version": settings.version,
            "mode": settings.app_mode.value,
            "docs": "/docs",
            "api": settings.api_prefix,
        }

    return app


# Create app instance
app = create_app()
