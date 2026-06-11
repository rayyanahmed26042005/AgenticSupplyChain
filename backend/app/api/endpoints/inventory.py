"""
Inventory management endpoints.
"""

from fastapi import APIRouter
from app.models.schemas import APIResponse

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/levels")
async def get_inventory_levels():
    """Get current inventory levels (from simulation or real data)."""
    from app.api.endpoints.simulation import _engine
    metrics = _engine.metrics_history
    if not metrics:
        return APIResponse(data={"message": "No inventory data. Run a simulation first."})

    latest = metrics[-1]
    return APIResponse(data={
        "current_inventory": latest.inventory,
        "day": latest.day,
        "demand": latest.demand,
        "stockout": latest.stockout,
        "trend": [
            {"day": m.day, "inventory": m.inventory, "demand": m.demand}
            for m in metrics[-30:]
        ],
    })


@router.get("/alerts")
async def get_inventory_alerts():
    """Get inventory alerts."""
    from app.api.endpoints.simulation import _engine
    metrics = _engine.metrics_history
    alerts = []

    for m in metrics[-14:]:
        if m.stockout:
            alerts.append({
                "type": "STOCKOUT",
                "severity": "HIGH",
                "day": m.day,
                "message": f"Stockout on day {m.day} — demand exceeded inventory",
            })
        elif m.inventory < m.demand * 0.2:
            alerts.append({
                "type": "LOW_STOCK",
                "severity": "MEDIUM",
                "day": m.day,
                "message": f"Low stock warning on day {m.day}",
            })

    return APIResponse(data={"alerts": alerts, "count": len(alerts)})
