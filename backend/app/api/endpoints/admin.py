"""
Admin endpoints - Mode switching, system configuration.
"""

from fastapi import APIRouter, HTTPException
from app.config import AppMode, DataSourceType
from app.core.app_modes import mode_manager
from app.core.data_manager import data_manager
from app.events.event_bus import event_bus
from app.models.schemas import ModeSwitchRequest, DataSourceSwitchRequest, APIResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/mode")
async def get_current_mode():
    """Get current application mode."""
    return APIResponse(data=mode_manager.get_mode_info())


@router.post("/mode")
async def switch_mode(request: ModeSwitchRequest):
    """Switch application mode."""
    try:
        new_mode = AppMode(request.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")

    result = mode_manager.switch_mode(new_mode)
    return APIResponse(data=result)


@router.post("/data-source")
async def switch_data_source(request: DataSourceSwitchRequest):
    """Switch data source."""
    try:
        new_source = DataSourceType(request.source)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid source: {request.source}")

    result = mode_manager.switch_data_source(new_source)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return APIResponse(data=result)


@router.get("/events")
async def get_recent_events(count: int = 50, event_type: str = None):
    """Get recent events."""
    events = event_bus.get_recent_events(count, event_type)
    return APIResponse(data={"events": events, "count": len(events)})


@router.get("/data-sources")
async def get_available_data_sources():
    """Get data sources available for current mode."""
    return APIResponse(data={
        "current": mode_manager.data_source.value,
        "available": mode_manager.get_available_data_sources(),
    })
