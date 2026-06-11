"""
Data ingestion and management endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any, List, Optional
import os
import shutil
import logging

from app.config import settings, DataSourceType
from app.core.data_manager import data_manager
from app.core.auth import get_owner_id
from app.agents.orchestrator import get_agent_orchestrator
from app.models.schemas import (
    ManualRecordRequest,
    ManualBatchRequest,
    DataIngestionRequest,
    MergeDatasetsRequest,
    APIResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["Data"])


@router.get("/status")
async def data_status(owner_id: str = Depends(get_owner_id)):
    """Get data manager status."""
    await data_manager.load_user_datasets_from_db(owner_id)
    return APIResponse(data=data_manager.get_status(owner_id))


@router.get("/datasets")
async def list_datasets(owner_id: str = Depends(get_owner_id)):
    """List all loaded datasets."""
    await data_manager.load_user_datasets_from_db(owner_id)
    return APIResponse(data=data_manager.get_current_datasets(owner_id))


@router.post("/upload")
async def upload_csv(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    dataset_name: Optional[str] = None,
    owner_id: str = Depends(get_owner_id)
):
    """Upload one or more CSV files."""
    uploaded_files = []
    if file is not None:
        uploaded_files.append(file)
    if files is not None:
        uploaded_files.extend(files)

    if not uploaded_files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results = []
    last_compiled = None

    await data_manager.load_user_datasets_from_db(owner_id)

    for u_file in uploaded_files:
        if not u_file.filename.endswith(".csv"):
            logger.warning(f"File {u_file.filename} is not a CSV. Skipping.")
            results.append({
                "filename": u_file.filename,
                "status": "error",
                "error": "Only CSV files are supported"
            })
            continue

        os.makedirs(settings.data_upload_path, exist_ok=True)
        filepath = os.path.join(settings.data_upload_path, u_file.filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(u_file.file, buffer)

        curr_dataset_name = dataset_name if (dataset_name and len(uploaded_files) == 1) else u_file.filename.replace(".csv", "")

        result = await data_manager.ingest_data(
            DataSourceType.CSV, filepath, curr_dataset_name, owner_id
        )

        if result.get("status") == "success":
            compiled = data_manager.compile_csv_simulation_result(owner_id, dataset_name=curr_dataset_name)
            if compiled:
                from app.simulation.state_manager import state_manager
                import uuid

                # Run agents on the CSV metrics
                env = {"metrics": compiled["metrics"], "disruptions": []}
                orchestrator = get_agent_orchestrator(owner_id)
                agent_result = await orchestrator.run_all_agents(env)
                compiled["agent_analysis"] = agent_result.get("summary", {})

                # Save state so it can be replayed and populated in history
                sim_id = f"csv-{str(uuid.uuid4())[:8]}"
                await state_manager.save_state(sim_id, compiled, label=f"CSV: {u_file.filename}", owner_id=owner_id)
                compiled["simulation_id"] = sim_id
                last_compiled = compiled

            results.append({
                "filename": u_file.filename,
                "dataset_name": curr_dataset_name,
                "status": "success",
                "rows": result.get("rows", 0)
            })
        else:
            results.append({
                "filename": u_file.filename,
                "status": "error",
                "error": result.get("error", "Unknown ingestion error")
            })

    if last_compiled:
        return APIResponse(data=last_compiled, message=f"Successfully ingested {len(uploaded_files)} file(s).")

    return APIResponse(data={"results": results}, message="Ingestion processed.")


@router.post("/manual/record")
async def add_manual_record(request: ManualRecordRequest, owner_id: str = Depends(get_owner_id)):
    """Add a manual data record (ingests row into any dataset)."""
    try:
        await data_manager.load_user_datasets_from_db(owner_id)
        result = await data_manager.add_row_to_dataset(request.dataset_name, request.record, owner_id)
        return APIResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/manual/batch")
async def add_manual_batch(request: ManualBatchRequest, owner_id: str = Depends(get_owner_id)):
    """Add multiple manual data records."""
    try:
        await data_manager.load_user_datasets_from_db(owner_id)
        state = data_manager._get_user_state(owner_id)
        if DataSourceType.MANUAL not in state["data_sources"]:
            await data_manager.initialize_data_source(DataSourceType.MANUAL, owner_id)

        ingester = state["data_sources"][DataSourceType.MANUAL]
        result = await ingester.add_batch(request.dataset_name, request.records)
        return APIResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ingest")
async def ingest_data(request: DataIngestionRequest, owner_id: str = Depends(get_owner_id)):
    """Ingest data from a specified source."""
    try:
        source_type = DataSourceType(request.source_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source type: {request.source_type}",
        )

    await data_manager.load_user_datasets_from_db(owner_id)
    result = await data_manager.ingest_data(
        source_type, request.source_path, request.dataset_name, owner_id
    )
    return APIResponse(data=result)


@router.get("/dataset/{name}")
async def get_dataset(name: str, owner_id: str = Depends(get_owner_id)):
    """Get a specific dataset (returns first 100 rows)."""
    await data_manager.load_user_datasets_from_db(owner_id)
    dataset = data_manager.get_dataset(name, owner_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found")

    # Convert to serializable format
    if hasattr(dataset, "to_dict"):
        data = dataset.head(100).to_dict(orient="records")
    elif isinstance(dataset, dict):
        data = dataset
    else:
        data = str(dataset)

    return APIResponse(data={"name": name, "rows": data})


@router.delete("/dataset/{name}")
async def delete_dataset(name: str, owner_id: str = Depends(get_owner_id)):
    """Delete a specific dataset from memory and MongoDB Atlas."""
    await data_manager.load_user_datasets_from_db(owner_id)
    success = await data_manager.delete_dataset(name, owner_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset '{name}'")
    return APIResponse(message=f"Dataset '{name}' deleted successfully.")


@router.post("/merge")
async def merge_datasets(request: MergeDatasetsRequest, owner_id: str = Depends(get_owner_id)):
    """Merge multiple datasets chronologically and run agent analysis."""
    if len(request.dataset_names) < 2:
        raise HTTPException(status_code=400, detail="At least two datasets must be specified for merging")
    
    try:
        await data_manager.load_user_datasets_from_db(owner_id)
        result = await data_manager.merge_datasets(request.dataset_names, request.merged_name, owner_id)
        return APIResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
