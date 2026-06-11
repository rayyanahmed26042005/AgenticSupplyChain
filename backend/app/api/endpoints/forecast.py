"""
Demand forecasting endpoints.
"""

from fastapi import APIRouter
from app.ml.demand_forecaster import DemandForecaster
from app.models.schemas import ForecastRequest, APIResponse

router = APIRouter(prefix="/forecast", tags=["Forecast"])

_forecaster = DemandForecaster()


@router.post("/demand")
async def forecast_demand(request: ForecastRequest):
    """Generate demand forecast."""
    if request.data:
        _forecaster.fit(request.data)

    result = _forecaster.forecast(horizon=request.horizon)
    return APIResponse(data=result)


@router.get("/accuracy")
async def forecast_accuracy():
    """Get forecast accuracy metrics."""
    return APIResponse(data=_forecaster.get_accuracy_metrics())
