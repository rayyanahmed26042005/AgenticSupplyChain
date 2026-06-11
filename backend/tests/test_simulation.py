import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_run_simulation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Start simulation
        payload = {
            "simulation_days": 10,
            "num_disruptions": 1,
            "base_demand": 500,
            "seed": 123
        }
        response = await ac.post("/api/v1/simulation/run", json=payload)
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert "simulation_id" in data
        assert "metrics" in data
        assert len(data["metrics"]) == 10
        assert "agent_analysis" in data
        
        # 2. Check history
        history_response = await ac.get("/api/v1/simulation/history")
        assert history_response.status_code == 200
        history_data = history_response.json()["data"]
        assert any(item["simulation_id"] == data["simulation_id"] for item in history_data)
        
        # 3. Retrieve by ID
        sim_id = data["simulation_id"]
        get_response = await ac.get(f"/api/v1/simulation/history/{sim_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["simulation_id"] == sim_id


@pytest.mark.asyncio
async def test_csv_and_explainability():
    from app.core.data_manager import data_manager
    import pandas as pd
    
    # 1. Populate mock CSV data in DataManager
    mock_data = pd.DataFrame([
        {
            "product_type": "Cosmetics",
            "sku": "SKU1",
            "price": 100.0,
            "number_of_products_sold": 120,
            "stock_levels": 50,
            "defect_rates": 1.5,
            "lead_time": 12,
            "costs": 45.0,
            "revenue_generated": 12000.0
        }
    ])
    
    # Manually insert into current_datasets
    data_manager.current_datasets["test_uploaded"] = mock_data
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Run agents with no environment passed (should read from data_manager)
        response = await ac.post("/api/v1/agents/run")
        assert response.status_code == 200
        result_data = response.json()["data"]
        assert "agents" in result_data
        
        # Test explain endpoint with the generated decision
        explain_response = await ac.post("/api/v1/agents/explain", json=result_data)
        assert explain_response.status_code == 200
        explain_data = explain_response.json()["data"]
        assert "business_impact" in explain_data
        assert "expected_service_level" in explain_data
        assert "stockout_probability" in explain_data
        assert "disruption_probability" in explain_data
        assert "agent_traces" in explain_data
        assert "feature_importance" in explain_data
        assert "alternatives_considered" in explain_data
        assert "event_log" in explain_data
        
    # Cleanup data_manager
    data_manager.current_datasets.clear()


@pytest.mark.asyncio
async def test_csv_upload_compilation(tmp_path):
    # Create a mock CSV file
    csv_file = tmp_path / "test_upload.csv"
    csv_file.write_text(
        "Product type,SKU,Price,Availability,Number of products sold,Revenue generated,Stock levels,Lead time,Costs\n"
        "Cosmetics,SKU1,100.0,Yes,120,12000.0,50,12,45.0\n"
    )
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Upload the mock CSV
        with open(csv_file, "rb") as f:
            files = {"file": ("test_upload.csv", f, "text/csv")}
            response = await ac.post("/api/v1/data/upload?dataset_name=test_upload_endpoint", files=files)
            
        assert response.status_code == 200
        result_data = response.json()["data"]
        
        # Verify compiled simulation keys
        assert "metrics" in result_data
        assert "statistics" in result_data
        assert "agent_analysis" in result_data
        assert len(result_data["metrics"]) == 1
        assert result_data["statistics"]["avg_demand"] == 120.0
        assert result_data["statistics"]["avg_inventory"] == 50.0
