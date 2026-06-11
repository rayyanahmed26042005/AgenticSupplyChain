"""
Unified Configuration for Agentic Supply Chain Orchestrator
Supports SIMULATION, REALTIME, and HYBRID modes with data source validation.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum


class AppMode(str, Enum):
    SIMULATION = "simulation"
    REALTIME = "realtime"
    HYBRID = "hybrid"


class DataSourceType(str, Enum):
    CSV = "csv"
    KAFKA = "kafka"
    API = "api"
    MANUAL = "manual"
    KAGGLE = "kaggle"
    DATABASE = "database"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # ============= MODE SETTINGS =============
    app_mode: AppMode = AppMode.SIMULATION
    data_source: DataSourceType = DataSourceType.MANUAL

    # ============= APP SETTINGS =============
    app_name: str = "Agentic Supply Chain Orchestrator"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # ============= DATABASE =============
    database_url: str = "sqlite+aiosqlite:///./data/supply_chain.db"
    database_echo: bool = False
    mongodb_uri: str = "mongodb+srv://supplychain:supply00@cluster0.8vsvicb.mongodb.net/?appName=Cluster0"
    jwt_secret: str = "supersecretjwtsecretkeysupplychainorchestrator12345!"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    # ============= REDIS/CACHE =============
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False
    cache_ttl: int = 300

    # ============= SIMULATION SETTINGS =============
    simulation_enabled: bool = True
    simulation_speed: float = 1.0
    preload_kaggle_data: bool = False
    kaggle_data_path: str = "./data/kaggle"
    simulation_seed: int = 42
    default_simulation_days: int = 90
    default_disruptions: int = 3

    # ============= DATA INGESTION =============
    data_upload_path: str = "./data/uploads"
    allowed_upload_extensions: List[str] = ["csv", "json", "parquet"]
    max_upload_size_mb: int = 500
    auto_validate_data: bool = True

    # ============= ML/AI SETTINGS =============
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    enable_explainability: bool = True
    use_llm_agents: bool = False  # False = rule-based agents, True = LLM-powered

    # ============= EVENT PROCESSING =============
    event_enabled: bool = True
    event_retention_days: int = 30
    max_event_history: int = 10000

    # ============= API SETTINGS =============
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["*"]

    # ============= LOGGING =============
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Factory function for settings with mode validation."""
    _settings = Settings()

    # Validate mode consistency
    if (
        _settings.app_mode == AppMode.SIMULATION
        and _settings.data_source == DataSourceType.KAFKA
    ):
        raise ValueError("Cannot use KAFKA data source in SIMULATION mode")

    return _settings


# Global settings instance
settings = get_settings()
