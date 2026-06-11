"""
Central API router aggregating all endpoint routers.
"""

from fastapi import APIRouter

from app.api.endpoints import health, data, simulation, forecast, supplier, agents, inventory, admin, auth

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(data.router)
api_router.include_router(simulation.router)
api_router.include_router(forecast.router)
api_router.include_router(supplier.router)
api_router.include_router(agents.router)
api_router.include_router(inventory.router)
api_router.include_router(admin.router)
api_router.include_router(auth.router)
