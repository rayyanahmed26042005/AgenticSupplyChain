"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============= Mode Schemas =============
class ModeSwitchRequest(BaseModel):
    mode: str = Field(..., description="Target mode: simulation, realtime, hybrid")


class DataSourceSwitchRequest(BaseModel):
    source: str = Field(..., description="Data source: csv, manual, kaggle, kafka, api")


# ============= Simulation Schemas =============
class SimulationRequest(BaseModel):
    simulation_days: int = Field(default=90, ge=1, le=365)
    num_disruptions: int = Field(default=3, ge=0, le=20)
    base_demand: float = Field(default=1000, gt=0)
    seed: int = Field(default=42)


class ScenarioCreateRequest(BaseModel):
    name: str
    description: str = ""
    simulation_days: int = 90
    base_demand: float = 1000
    num_disruptions: int = 3
    seed: int = 42
    tags: List[str] = []


# ============= Data Schemas =============
class ManualRecordRequest(BaseModel):
    dataset_name: str
    record: Dict[str, Any]


class ManualBatchRequest(BaseModel):
    dataset_name: str
    records: List[Dict[str, Any]]


class DataIngestionRequest(BaseModel):
    source_type: str
    source_path: str
    dataset_name: str


class MergeDatasetsRequest(BaseModel):
    dataset_names: List[str]
    merged_name: str


# ============= Forecast Schemas =============
class ForecastRequest(BaseModel):
    horizon: int = Field(default=7, ge=1, le=90)
    data: Optional[List[float]] = None


# ============= Supplier Schemas =============
class SupplierRiskRequest(BaseModel):
    defect_rate: float = 0
    lead_time_variance: float = 0
    on_time_delivery: float = 0.95
    financial_stability: float = 0.8
    geographic_risk: float = 0.2
    diversification: float = 0.7


# ============= Response Schemas =============
class APIResponse(BaseModel):
    status: str = "success"
    data: Any = None
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    status: str = "error"
    error: str
    detail: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
