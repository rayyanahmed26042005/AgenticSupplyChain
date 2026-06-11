"""
Supplier risk management endpoints.
"""

from fastapi import APIRouter
from app.ml.risk_predictor import risk_predictor
from app.models.schemas import SupplierRiskRequest, APIResponse

router = APIRouter(prefix="/supplier", tags=["Supplier"])


@router.post("/risk")
async def predict_supplier_risk(request: SupplierRiskRequest):
    """Predict supplier risk score."""
    result = risk_predictor.predict_risk(request.model_dump())
    return APIResponse(data=result)


@router.post("/risk/batch")
async def batch_risk_prediction(suppliers: list[SupplierRiskRequest]):
    """Predict risk for multiple suppliers."""
    data = [s.model_dump() for s in suppliers]
    results = risk_predictor.batch_predict(data)
    return APIResponse(data=results)
