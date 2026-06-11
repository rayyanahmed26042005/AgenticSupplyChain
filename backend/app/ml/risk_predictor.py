"""
Risk Predictor - Supplier risk scoring with weighted feature analysis.
"""

import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RiskPredictor:
    """Predict supplier risk using weighted multi-factor scoring."""

    def __init__(self):
        self.weights = {
            "defect_rate": 0.25,
            "lead_time_variance": 0.20,
            "on_time_delivery": 0.20,
            "financial_stability": 0.15,
            "geographic_risk": 0.10,
            "diversification": 0.10,
        }
        self.risk_history: List[Dict[str, Any]] = []

    def predict_risk(self, supplier_data: Dict[str, float]) -> Dict[str, Any]:
        """Calculate composite risk score for a supplier with critical overrides."""
        scores = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for factor, weight in self.weights.items():
            if factor in supplier_data:
                raw_value = supplier_data[factor]
                normalized = self._normalize_factor(factor, raw_value)
                scores[factor] = {
                    "raw": round(raw_value, 3),
                    "normalized": round(normalized, 3),
                    "weight": weight,
                    "contribution": round(normalized * weight, 3),
                }
                weighted_sum += normalized * weight
                total_weight += weight

        composite_risk = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Critical Overrides: If any single normalized risk factor is extremely high (e.g. defect rate > 75%), 
        # it should elevate the overall risk score immediately to prevent dilution.
        max_normalized = max([f["normalized"] for f in scores.values()]) if scores else 0.0
        if max_normalized > 0.75:
            composite_risk = max(composite_risk, max_normalized)

        result = {
            "composite_risk": round(composite_risk, 3),
            "risk_level": self._risk_level(composite_risk),
            "factor_scores": scores,
            "top_risk_factors": self._get_top_factors(scores),
            "recommendation": self._get_recommendation(composite_risk, scores),
        }

        self.risk_history.append(result)
        return result

    def _normalize_factor(self, factor: str, value: float) -> float:
        """Normalize factor value to 0-1 risk scale (higher = riskier)."""
        normalizers = {
            "defect_rate": lambda v: min(1.0, v / 10.0),
            "lead_time_variance": lambda v: min(1.0, v / 15.0),
            "on_time_delivery": lambda v: 1.0 - min(1.0, max(0, v)),
            "financial_stability": lambda v: 1.0 - min(1.0, max(0, v)),
            "geographic_risk": lambda v: min(1.0, max(0, v)),
            "diversification": lambda v: 1.0 - min(1.0, max(0, v)),
        }
        normalizer = normalizers.get(factor, lambda v: min(1.0, max(0, v)))
        return normalizer(value)

    def _risk_level(self, score: float) -> str:
        if score > 0.75:
            return "CRITICAL"
        elif score > 0.5:
            return "HIGH"
        elif score > 0.25:
            return "MEDIUM"
        return "LOW"

    def _get_top_factors(self, scores: Dict) -> List[Dict]:
        """Get top contributing risk factors."""
        sorted_factors = sorted(
            scores.items(),
            key=lambda x: x[1]["contribution"],
            reverse=True,
        )
        return [
            {"factor": name, **data}
            for name, data in sorted_factors[:3]
        ]

    def _get_recommendation(self, risk: float, scores: Dict) -> str:
        if risk > 0.75:
            return "Critical risk level. Consider replacing or significantly reducing dependency on this supplier."
        elif risk > 0.5:
            return "High risk detected. Activate backup suppliers and increase monitoring."
        elif risk > 0.25:
            return "Moderate risk. Monitor key risk factors and prepare contingency plans."
        return "Low risk. Maintain current supplier relationship."

    def batch_predict(self, suppliers: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Predict risk for multiple suppliers."""
        return [self.predict_risk(s) for s in suppliers]


# Global instance
risk_predictor = RiskPredictor()
