from fastapi import APIRouter, HTTPException, Depends
from app.agents.orchestrator import get_agent_orchestrator
from app.ml.explainability import decision_explainer
from app.models.schemas import APIResponse
from app.core.auth import get_owner_id
from app.core.data_manager import data_manager

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/status")
async def get_all_agent_status(owner_id: str = Depends(get_owner_id)):
    """Get status of all agents."""
    orchestrator = get_agent_orchestrator(owner_id)
    return APIResponse(data=orchestrator.get_all_states())


@router.get("/{agent_name}/status")
async def get_agent_status(agent_name: str, owner_id: str = Depends(get_owner_id)):
    """Get status of a specific agent."""
    orchestrator = get_agent_orchestrator(owner_id)
    state = orchestrator.get_agent_state(agent_name)
    if "error" in state:
        raise HTTPException(status_code=404, detail=state["error"])
    return APIResponse(data=state)


@router.get("/decisions")
async def get_recent_decisions(count: int = 10, owner_id: str = Depends(get_owner_id)):
    """Get recent orchestration decisions."""
    orchestrator = get_agent_orchestrator(owner_id)
    return APIResponse(data=orchestrator.get_recent_decisions(count))


@router.get("/{agent_name}/decisions")
async def get_agent_decisions(agent_name: str, count: int = 10, owner_id: str = Depends(get_owner_id)):
    """Get decisions from a specific agent."""
    orchestrator = get_agent_orchestrator(owner_id)
    return APIResponse(data=orchestrator.get_agent_decisions(agent_name, count))


@router.get("/performance")
async def get_performance_summary(owner_id: str = Depends(get_owner_id)):
    """Get agent performance summary."""
    orchestrator = get_agent_orchestrator(owner_id)
    return APIResponse(data=orchestrator.get_performance_summary())


@router.post("/run")
async def run_agents(environment: dict = None, owner_id: str = Depends(get_owner_id)):
    """Manually trigger an agent cycle."""
    orchestrator = get_agent_orchestrator(owner_id)
    if environment:
        env = environment
    else:
        await data_manager.load_user_datasets_from_db(owner_id)
        csv_metrics = data_manager.get_latest_metrics_from_csv(owner_id)
        if csv_metrics:
            env = {"metrics": csv_metrics, "disruptions": []}
        else:
            env = {"metrics": [], "disruptions": []}

    result = await orchestrator.run_all_agents(env)
    return APIResponse(data=result)


@router.post("/reset")
async def reset_agents(owner_id: str = Depends(get_owner_id)):
    """Reset all agents."""
    orchestrator = get_agent_orchestrator(owner_id)
    orchestrator.reset_all()
    return APIResponse(message="All agents reset")


@router.post("/explain")
async def explain_decision(decision: dict):
    """Get explainability for a decision."""
    explanation = decision_explainer.explain_decision(decision)
    return APIResponse(data=explanation)
