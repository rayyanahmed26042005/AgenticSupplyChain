"""
Simulation endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any
import logging
import uuid

from app.simulation.engine import get_simulation_engine
from app.simulation.scenarios import ScenarioManager
from app.simulation.disruptions import DisruptionGenerator, DisruptionType
from app.simulation.state_manager import state_manager
from app.core.auth import get_owner_id
from app.core.mongodb import mongodb
from app.agents.orchestrator import get_agent_orchestrator
from app.models.schemas import SimulationRequest, ScenarioCreateRequest, APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulation", tags=["Simulation"])

# Shared managers
_scenario_mgr = ScenarioManager()
_disruption_gen = DisruptionGenerator()


@router.post("/run")
async def run_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    owner_id: str = Depends(get_owner_id)
):
    """Run a supply chain simulation."""
    engine = get_simulation_engine(owner_id)
    if engine.state.value == "running":
        raise HTTPException(status_code=409, detail="Simulation already running")

    result = await engine.run_simulation(
        simulation_days=request.simulation_days,
        num_disruptions=request.num_disruptions,
        base_demand=request.base_demand,
        seed=request.seed,
    )

    # Run agents on the simulation data
    if result.get("metrics"):
        env = {"metrics": result["metrics"], "disruptions": result["disruptions"]}
        orchestrator = get_agent_orchestrator(owner_id)
        agent_result = await orchestrator.run_all_agents(env)
        result["agent_analysis"] = agent_result.get("summary", {})

    # Save state
    sim_id = f"sim-{str(uuid.uuid4())[:8]}"
    await state_manager.save_state(sim_id, result, owner_id=owner_id)

    return APIResponse(data={"simulation_id": sim_id, **result})


@router.get("/latest")
async def get_latest_simulation(owner_id: str = Depends(get_owner_id)):
    """Get the latest completed simulation result (from engine or MongoDB)."""
    # 1. Try to get from active engine if completed
    engine = get_simulation_engine(owner_id)
    if engine.state.value == "completed" and engine.metrics_history:
        return APIResponse(data=engine._compile_results())

    # 2. Otherwise, fetch the latest saved state from MongoDB
    if mongodb.db is not None:
        try:
            doc = await mongodb.db["simulations"].find_one(
                {"owner_id": owner_id},
                sort=[("saved_at", -1)]
            )
            if doc:
                doc.pop("_id", None)
                return APIResponse(data=doc["state"])
        except Exception as e:
            logger.error(f"Failed to fetch latest simulation from MongoDB: {e}")

    return APIResponse(data=None)


@router.get("/state")
async def get_simulation_state(owner_id: str = Depends(get_owner_id)):
    """Get current simulation state."""
    engine = get_simulation_engine(owner_id)
    return APIResponse(data=engine.get_state())


@router.post("/pause")
async def pause_simulation(owner_id: str = Depends(get_owner_id)):
    """Pause running simulation."""
    engine = get_simulation_engine(owner_id)
    engine.pause()
    return APIResponse(data=engine.get_state(), message="Simulation paused")


@router.post("/resume")
async def resume_simulation(owner_id: str = Depends(get_owner_id)):
    """Resume paused simulation."""
    engine = get_simulation_engine(owner_id)
    engine.resume()
    return APIResponse(data=engine.get_state(), message="Simulation resumed")


@router.post("/stop")
async def stop_simulation(owner_id: str = Depends(get_owner_id)):
    """Stop simulation."""
    engine = get_simulation_engine(owner_id)
    engine.stop()
    return APIResponse(data=engine.get_state(), message="Simulation stopped")


# ============= Scenarios =============
@router.get("/scenarios")
async def list_scenarios():
    """List all available scenarios."""
    return APIResponse(data=_scenario_mgr.list_scenarios())


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario."""
    try:
        return APIResponse(data=_scenario_mgr.get_scenario(scenario_id))
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")


@router.post("/scenarios")
async def create_scenario(request: ScenarioCreateRequest):
    """Create a custom scenario."""
    result = _scenario_mgr.create_custom_scenario(
        name=request.name,
        description=request.description,
        simulation_days=request.simulation_days,
        base_demand=request.base_demand,
        num_disruptions=request.num_disruptions,
        seed=request.seed,
        tags=request.tags,
    )
    return APIResponse(data=result, message="Scenario created")


@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: str, owner_id: str = Depends(get_owner_id)):
    """Run a predefined scenario."""
    try:
        scenario = _scenario_mgr.get_scenario(scenario_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Scenario not found")

    engine = get_simulation_engine(owner_id)
    result = await engine.run_simulation(
        simulation_days=scenario["simulation_days"],
        num_disruptions=scenario["num_disruptions"],
        base_demand=scenario["base_demand"],
        seed=scenario["seed"],
    )

    sim_id = f"sim-{scenario_id}-{str(uuid.uuid4())[:6]}"
    await state_manager.save_state(sim_id, result, label=scenario["name"], owner_id=owner_id)

    return APIResponse(data={"simulation_id": sim_id, **result})


# ============= Disruptions =============
@router.get("/disruptions/types")
async def get_disruption_types():
    """Get all disruption types."""
    return APIResponse(data=_disruption_gen.get_disruption_types())


@router.post("/disruptions/generate")
async def generate_disruption(disruption_type: str = "supplier_failure", severity: float = None):
    """Generate a disruption."""
    try:
        dtype = DisruptionType(disruption_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid type: {disruption_type}")

    result = _disruption_gen.generate(dtype, severity=severity)
    return APIResponse(data=result)


# ============= State =============
@router.get("/history")
async def simulation_history(owner_id: str = Depends(get_owner_id)):
    """Get saved simulation states."""
    return APIResponse(data=await state_manager.list_saved_states(owner_id))


@router.get("/history/{simulation_id}")
async def get_saved_simulation(simulation_id: str, owner_id: str = Depends(get_owner_id)):
    """Get a saved simulation state."""
    state = await state_manager.load_state(simulation_id, owner_id)
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return APIResponse(data=state)
