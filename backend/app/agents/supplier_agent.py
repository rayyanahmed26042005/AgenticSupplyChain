"""
Supplier Agent - Monitors supplier risk, recommends diversification, predicts disruptions.
Integrates with RiskPredictor ML model for composite multi-factor risk scoring.
"""

from typing import Dict, Any, List
import numpy as np
import logging

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.utils.llm_helper import call_groq_llm

logger = logging.getLogger(__name__)


class SupplierAgent(BaseAgent):
    """Agent responsible for supplier risk management, optimization, and disruption prediction."""

    def __init__(self):
        super().__init__(
            agent_id="supplier-agent-001",
            name="Supplier Risk Manager",
            role="supplier_management",
        )
        self.risk_threshold = 0.5
        self.critical_risk_threshold = 0.75
        self._risk_predictor = None

    def _get_risk_predictor(self):
        """Lazy-load the RiskPredictor ML model."""
        if self._risk_predictor is None:
            try:
                from app.ml.risk_predictor import RiskPredictor
                self._risk_predictor = RiskPredictor()
            except Exception as e:
                logger.warning(f"Could not load RiskPredictor: {e}")
        return self._risk_predictor

    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract supplier-relevant data from environment."""
        import math
        def safe_val(v, default=0.0):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            try:
                f_val = float(v)
                return default if math.isnan(f_val) else f_val
            except Exception:
                return default

        metrics = environment.get("metrics", [])
        disruptions = environment.get("disruptions", [])
        recent = metrics[-7:] if len(metrics) >= 7 else metrics
        extended = metrics[-21:] if len(metrics) >= 21 else metrics

        risks = [safe_val(m.get("supplier_risk"), 0.0) for m in recent]
        otd_rates = [safe_val(m.get("on_time_delivery"), 1.0) for m in recent]
        costs = [safe_val(m.get("cost"), 50.0) for m in recent]

        # Extended risk history for disruption prediction
        extended_risks = [safe_val(m.get("supplier_risk"), 0.0) for m in extended]

        # ML-based composite risk scoring
        ml_risk_result = None
        predictor = self._get_risk_predictor()
        if predictor and recent:
            try:
                latest = recent[-1]
                supplier_data = {
                    "defect_rate": latest.get("supplier_risk", 0) * 10,  # Scale to defect %
                    "lead_time_variance": abs(latest.get("demand", 0) - np.mean([m.get("demand", 0) for m in recent])) / max(1, np.mean([m.get("demand", 0) for m in recent])) * 15,
                    "on_time_delivery": latest.get("on_time_delivery", 1.0),
                    "financial_stability": max(0, 1.0 - latest.get("supplier_risk", 0)),
                    "geographic_risk": latest.get("supplier_risk", 0) * 0.5,
                    "diversification": 0.6,  # Default moderate diversification
                }
                ml_risk_result = predictor.predict_risk(supplier_data)
            except Exception as e:
                logger.debug(f"ML risk prediction failed: {e}")

        # Predictive disruption modeling — detect risk acceleration
        disruption_predicted = False
        disruption_prediction_horizon = 0
        if len(extended_risks) >= 7:
            # Check if risk is accelerating (2nd derivative positive)
            recent_trend = self._calculate_trend(extended_risks[-7:])
            older_trend = self._calculate_trend(extended_risks[:7]) if len(extended_risks) >= 14 else 0
            risk_acceleration = recent_trend - older_trend

            # Check risk velocity (moving average increasing)
            if len(extended_risks) >= 14:
                recent_avg = np.mean(extended_risks[-7:])
                older_avg = np.mean(extended_risks[:7])
                risk_velocity = recent_avg - older_avg
            else:
                risk_velocity = recent_trend

            # Predict disruption if risk is accelerating AND above threshold
            if (risk_acceleration > 0.02 and np.mean(risks) > 0.2) or \
               (risk_velocity > 0.1 and np.mean(risks) > 0.3):
                disruption_predicted = True
                # Estimate days until potential disruption (2-6 weeks)
                disruption_prediction_horizon = max(14, min(42, int(
                    (self.critical_risk_threshold - np.mean(risks)) / max(0.01, risk_velocity) * 7
                )))

        return {
            "current_risk": risks[-1] if risks else 0,
            "avg_risk": np.mean(risks) if risks else 0,
            "risk_trend": self._calculate_trend(risks),
            "avg_otd": np.mean(otd_rates) if otd_rates else 1.0,
            "active_disruptions": len([d for d in disruptions if not d.get("resolved")]),
            "disruption_types": [d.get("type") for d in disruptions[-5:]],
            "total_disruptions": len(disruptions),
            "ml_risk_result": ml_risk_result,
            "disruption_predicted": disruption_predicted,
            "disruption_prediction_horizon": disruption_prediction_horizon,
            "risk_acceleration": risk_acceleration if len(extended_risks) >= 7 else 0,
        }

    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Make supplier management decisions with ML risk scoring and disruption prediction."""
        current_risk = perception["current_risk"]
        avg_risk = perception["avg_risk"]
        risk_trend = perception["risk_trend"]
        avg_otd = perception["avg_otd"]
        active_disruptions = perception["active_disruptions"]
        ml_risk_result = perception.get("ml_risk_result")
        disruption_predicted = perception.get("disruption_predicted", False)
        prediction_horizon = perception.get("disruption_prediction_horizon", 0)

        # Use ML composite risk if available, otherwise use simple risk
        if ml_risk_result:
            composite_risk = ml_risk_result.get("composite_risk", current_risk)
            risk_method = "ml_weighted_multi_factor"
            top_risk_factors = ml_risk_result.get("top_risk_factors", [])
        else:
            composite_risk = current_risk
            risk_method = "threshold_based"
            top_risk_factors = []

        # Risk assessment (using ML risk if available)
        risk_level = self._assess_risk_level(composite_risk, risk_trend, active_disruptions, disruption_predicted)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, avg_otd, active_disruptions, risk_trend, disruption_predicted
        )

        # Disruption probability — proportional to overall composite risk
        disruption_probability = round(max(1.0, min(95.0, composite_risk * 100.0)), 1)

        # Risk score out of 100 (inverted — 100 = highest risk)
        risk_score_100 = round(composite_risk * 100, 0)

        # Generate reasoning explaining the direct mathematical relationship of risk variables
        rule_reasoning = self._generate_reasoning(risk_level, perception, composite_risk, disruption_probability)
        reasoning = rule_reasoning

        if settings.use_llm_agents:
            disruption_text = ""
            if disruption_predicted:
                disruption_text = f"\n- ⚠️ DISRUPTION PREDICTED in ~{prediction_horizon} days (risk acceleration detected)"
            prompt = (
                f"As a Supplier Risk Management Agent, analyze this supply chain risk state:\n"
                f"- Assigned Risk Level: {risk_level}\n"
                f"- Current Risk Score: {composite_risk:.2%}\n"
                f"- Risk Method: {risk_method}\n"
                f"- Risk Trend: {'increasing' if risk_trend > 0.02 else 'decreasing' if risk_trend < -0.02 else 'stable'}\n"
                f"- Average On-Time Delivery (OTD): {avg_otd:.2%}\n"
                f"- Active Disruptions Count: {active_disruptions}"
                f"{disruption_text}\n"
                f"- Chosen Core Action: {recommendations[0]['action'] if recommendations else 'monitor'}\n"
                f"Explain the reasoning and supplier recommendations in one short, professional sentence. Ensure you explain that defect_rate is the primary driver scaling the Supplier Risk Score to {risk_score_100:.0f}/100 and yielding a {disruption_probability:.0f}% disruption probability."
            )
            llm_reasoning = await call_groq_llm(prompt, system_prompt="You are an AI Supplier Risk Manager Agent in a supply chain system.")
            if llm_reasoning:
                reasoning = llm_reasoning

        # Confidence based on data quality and ML availability
        base_confidence = 0.6 if risk_method == "threshold_based" else 0.8
        confidence = round(min(0.95, base_confidence + (0.1 if not disruption_predicted else -0.05)), 2)

        # Primary risk factor — determine the most significant contributor
        if top_risk_factors and len(top_risk_factors) > 0:
            primary_risk_factor = top_risk_factors[0].get("factor", "Supplier Concentration")
        elif avg_otd < 0.85:
            primary_risk_factor = "On-Time Delivery"
        elif active_disruptions > 0:
            primary_risk_factor = "Active Disruptions"
        elif disruption_predicted:
            primary_risk_factor = "Predicted Disruption"
        elif risk_trend > 0.02:
            primary_risk_factor = "Risk Acceleration"
        elif composite_risk > 0.5:
            primary_risk_factor = "Supplier Concentration"
        else:
            primary_risk_factor = "None (Stable)"

        decision = {
            "risk_level": risk_level,
            "current_risk_score": round(composite_risk, 3),
            "risk_score_100": int(risk_score_100),
            "risk_trend": "increasing" if risk_trend > 0.02 else "decreasing" if risk_trend < -0.02 else "stable",
            "on_time_delivery_avg": round(avg_otd, 3),
            "active_disruptions": active_disruptions,
            "action": recommendations[0]["action"] if recommendations else "monitor",
            "recommendations": recommendations,
            "risk_method": risk_method,
            "top_risk_factors": [f.get("factor", "") for f in top_risk_factors[:3]],
            "primary_risk_factor": primary_risk_factor,
            "disruption_predicted": disruption_predicted,
            "disruption_prediction_horizon": prediction_horizon,
            "disruption_probability": disruption_probability,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        import math
        def safe_int(v, default=0):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            try:
                return int(v)
            except Exception:
                return default

        self.performance_metrics["supplier_risk_score"] = f"{safe_int(risk_score_100)} / 100"
        self.performance_metrics["risk_level"] = risk_level
        self.performance_metrics["primary_risk_factor"] = primary_risk_factor
        self.performance_metrics["on_time_delivery"] = f"{safe_int(round(avg_otd * 100, 0))}%"
        self.performance_metrics["disruption_probability"] = f"{safe_int(disruption_probability)}%"

        return decision

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute supplier decision."""
        return {
            "action_taken": decision["action"],
            "risk_level": decision["risk_level"],
            "recommendations_count": len(decision["recommendations"]),
            "disruption_predicted": decision.get("disruption_predicted", False),
            "status": "executed",
        }

    def _assess_risk_level(self, risk: float, trend: float, active_disruptions: int = 0, disruption_predicted: bool = False) -> str:
        """Assess overall risk level based on composite risk, trend, active disruptions, and disruption prediction."""
        score = risk
        if disruption_predicted:
            score = max(score, 0.45)
        if active_disruptions > 0:
            if active_disruptions >= 2:
                score = max(score, 0.80)
            else:
                score = max(score, 0.55)

        if score > self.critical_risk_threshold:
            return "CRITICAL"
        elif score > self.risk_threshold or (score > 0.35 and trend > 0.05):
            return "HIGH"
        elif score > 0.25:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_recommendations(
        self, risk_level: str, otd: float, disruptions: int, trend: float,
        disruption_predicted: bool = False,
    ) -> List[Dict]:
        """Generate actionable recommendations."""
        recs = []

        if risk_level in ("CRITICAL", "HIGH"):
            recs.append({
                "action": "diversify_suppliers",
                "priority": "HIGH",
                "description": "Activate backup suppliers to reduce concentration risk",
            })
            recs.append({
                "action": "increase_safety_stock",
                "priority": "HIGH",
                "description": "Increase buffer inventory to mitigate supply disruption",
            })

        if otd < 0.85:
            recs.append({
                "action": "review_logistics",
                "priority": "MEDIUM",
                "description": "Review shipping routes and carrier performance",
            })

        if disruptions > 0:
            recs.append({
                "action": "review_backups",
                "priority": "MEDIUM",
                "description": "Active disruption detected — review backup suppliers within 72 hours",
            })
            if disruptions > 2:
                recs.append({
                    "action": "escalate_review",
                    "priority": "HIGH",
                    "description": "Multiple active disruptions — escalate for management review",
                })

        if disruption_predicted:
            recs.append({
                "action": "activate_contingency",
                "priority": "HIGH",
                "description": "Predictive model indicates potential disruption — activate contingency planning",
            })
            recs.append({
                "action": "review_backups",
                "priority": "HIGH",
                "description": "Potential disruption predicted — review backup suppliers within 72 hours",
            })

        if trend > 0.05:
            recs.append({
                "action": "proactive_monitoring",
                "priority": "MEDIUM",
                "description": "Risk is trending upward — increase monitoring frequency",
            })

        if not recs:
            recs.append({
                "action": "monitor",
                "priority": "LOW",
                "description": "Supplier performance within acceptable parameters",
            })

        return recs

    def _calculate_trend(self, values: list) -> float:
        if len(values) < 3:
            return 0.0
        x = np.arange(len(values))
        try:
            coeffs = np.polyfit(x, values, 1)
            return coeffs[0]
        except Exception:
            return 0.0

    def _generate_reasoning(self, risk_level: str, perception: Dict, composite_risk: float, disruption_probability: float) -> str:
        current_risk = perception["current_risk"]
        disruption_predicted = perception.get("disruption_predicted", False)
        horizon = perception.get("disruption_prediction_horizon", 0)

        explanation = (
            f"Supplier risk is {risk_level} (overall score: {composite_risk*100:.0f}/100) driven by high quality defect rate ({current_risk*100:.0f}%), "
            f"yielding a {disruption_probability:.0f}% disruption probability. "
        )
        if disruption_predicted:
            explanation += f"Predictive model flags risk acceleration: potential disruption in ~{horizon} days."
        elif risk_level in ("CRITICAL", "HIGH"):
            explanation += "Immediate diversification and split ordering required to mitigate risk."
        else:
            explanation += "Maintain monitoring."
        return explanation
