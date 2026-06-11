"""
Data Manager - Orchestrates data flow between sources and modes.
Handles data ingestion, validation, caching, and mode-specific processing.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.config import DataSourceType, AppMode, settings
from app.core.app_modes import mode_manager

logger = logging.getLogger(__name__)


class DataManager:
    """
    Orchestrates data flow between different sources and modes.
    """

    def __init__(self):
        # Maps owner_id -> Dict containing data_sources, data_cache, ingestion_status, current_datasets
        self.user_states: Dict[str, Dict[str, Any]] = {}

    def _get_user_state(self, owner_id: str) -> Dict[str, Any]:
        if owner_id not in self.user_states:
            self.user_states[owner_id] = {
                "data_sources": {},
                "data_cache": {},
                "ingestion_status": {},
                "current_datasets": {},
            }
        return self.user_states[owner_id]

    @property
    def current_datasets(self) -> Dict[str, Any]:
        return self._get_user_state("guest")["current_datasets"]

    @property
    def data_cache(self) -> Dict[str, Dict[str, Any]]:
        return self._get_user_state("guest")["data_cache"]

    @property
    def ingestion_status(self) -> Dict[DataSourceType, Dict[str, Any]]:
        return self._get_user_state("guest")["ingestion_status"]

    @property
    def data_sources(self) -> Dict[DataSourceType, Any]:
        return self._get_user_state("guest")["data_sources"]

    async def initialize_data_source(self, source_type: DataSourceType, owner_id: str = "guest") -> bool:
        """Initialize selected data source."""
        if not mode_manager.can_use_data_source(source_type):
            logger.error(
                f"{source_type.value} not compatible with "
                f"{mode_manager.current_mode.value} mode"
            )
            return False

        try:
            logger.info(f"Initializing {source_type.value} data source for owner {owner_id}...")

            if source_type == DataSourceType.CSV:
                await self._init_csv_source(owner_id)
            elif source_type == DataSourceType.MANUAL:
                await self._init_manual_source(owner_id)
            elif source_type == DataSourceType.KAGGLE:
                await self._init_kaggle_source(owner_id)
            elif source_type == DataSourceType.KAFKA:
                await self._init_kafka_source(owner_id)
            elif source_type == DataSourceType.API:
                await self._init_api_source(owner_id)
            elif source_type == DataSourceType.DATABASE:
                await self._init_database_source(owner_id)

            state = self._get_user_state(owner_id)
            state["ingestion_status"][source_type] = {
                "initialized": True,
                "timestamp": datetime.now().isoformat(),
                "status": "ready",
            }
            logger.info(f"✅ {source_type.value} data source initialized for owner {owner_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize {source_type.value}: {e}")
            state = self._get_user_state(owner_id)
            state["ingestion_status"][source_type] = {
                "initialized": False,
                "error": str(e),
            }
            return False

    async def _init_csv_source(self, owner_id: str = "guest"):
        from app.data.ingestion.csv_ingester import CSVIngester
        state = self._get_user_state(owner_id)
        state["data_sources"][DataSourceType.CSV] = CSVIngester()

    async def _init_manual_source(self, owner_id: str = "guest"):
        from app.data.ingestion.manual_ingester import ManualIngester
        state = self._get_user_state(owner_id)
        ingester = ManualIngester()
        await ingester.load_buffers()
        state["data_sources"][DataSourceType.MANUAL] = ingester

    async def _init_kaggle_source(self, owner_id: str = "guest"):
        from app.data.ingestion.csv_ingester import KaggleDataLoader
        state = self._get_user_state(owner_id)
        loader = KaggleDataLoader(data_path=settings.kaggle_data_path)
        state["data_sources"][DataSourceType.KAGGLE] = loader

        if settings.preload_kaggle_data:
            data = await loader.ingest("all")
            if isinstance(data, dict):
                state["current_datasets"].update(data)

    async def _init_kafka_source(self, owner_id: str = "guest"):
        from app.data.ingestion.kafka_ingester import KafkaIngester
        state = self._get_user_state(owner_id)
        state["data_sources"][DataSourceType.KAFKA] = KafkaIngester()

    async def _init_api_source(self, owner_id: str = "guest"):
        from app.data.ingestion.api_ingester import APIIngester
        state = self._get_user_state(owner_id)
        state["data_sources"][DataSourceType.API] = APIIngester()

    async def _init_database_source(self, owner_id: str = "guest"):
        pass  # Database source uses SQLAlchemy directly

    async def ingest_data(
        self,
        source_type: DataSourceType,
        source_path_or_config: str,
        dataset_name: str,
        owner_id: str = "guest",
    ) -> Dict[str, Any]:
        """Ingest data from specified source."""
        state = self._get_user_state(owner_id)
        if source_type not in state["data_sources"]:
            await self.initialize_data_source(source_type, owner_id)

        ingester = state["data_sources"].get(source_type)
        if not ingester:
            raise ValueError(f"Data source {source_type.value} not initialized")

        logger.info(f"Ingesting data from {source_type.value} for owner {owner_id}: {source_path_or_config}")

        try:
            data = await ingester.ingest(source_path_or_config)

            # Validate
            if settings.auto_validate_data:
                validation_result = await self._validate_data(data)
                if not validation_result["valid"]:
                    logger.warning(f"Validation issues: {validation_result['errors']}")

            # Store
            state["current_datasets"][dataset_name] = data
            row_count = len(data) if hasattr(data, "__len__") else 0
            state["data_cache"][dataset_name] = {
                "source": source_type.value,
                "timestamp": datetime.now().isoformat(),
                "rows": row_count,
            }

            # Save to MongoDB if active
            await self._save_dataset_to_db(dataset_name, data, source_type.value, owner_id)

            logger.info(f"✅ Data ingested: {dataset_name} ({row_count} rows) for owner {owner_id}")

            return {
                "status": "success",
                "dataset_name": dataset_name,
                "source": source_type.value,
                "rows": row_count,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Data ingestion failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _validate_data(self, data: Any) -> Dict[str, Any]:
        """Validate ingested data."""
        from app.data.validation.validators import DataValidator

        validator = DataValidator()
        return validator.validate(data)

    def get_current_datasets(self, owner_id: str = "guest") -> Dict[str, Dict[str, Any]]:
        """Get metadata of currently loaded datasets."""
        state = self._get_user_state(owner_id)
        return state["data_cache"]

    def get_dataset(self, name: str, owner_id: str = "guest") -> Optional[Any]:
        """Get specific dataset by name."""
        state = self._get_user_state(owner_id)
        return state["current_datasets"].get(name)

    def get_all_datasets(self, owner_id: str = "guest") -> Dict[str, Any]:
        """Get all loaded datasets."""
        state = self._get_user_state(owner_id)
        return state["current_datasets"]

    def get_status(self, owner_id: str = "guest") -> Dict[str, Any]:
        """Get overall data manager status."""
        state = self._get_user_state(owner_id)
        return {
            "mode": mode_manager.current_mode.value,
            "data_source": mode_manager.data_source.value,
            "initialized_sources": {
                k.value: v for k, v in state["ingestion_status"].items()
            },
            "loaded_datasets": list(state["data_cache"].keys()),
            "dataset_count": len(state["current_datasets"]),
        }

    def get_latest_metrics_from_csv(self, owner_id: str = "guest", dataset_name: Optional[str] = None) -> Optional[list]:
        """Get latest ingested CSV data mapped to simulation metrics format."""
        state = self._get_user_state(owner_id)
        if not state["current_datasets"]:
            return None

        # Get the target dataset
        if dataset_name is None:
            dataset_name = next(iter(state["current_datasets"].keys()))
        df = state["current_datasets"].get(dataset_name)

        # Check if df is a pandas DataFrame
        if df is None or not hasattr(df, "iterrows"):
            return None

        metrics = []
        import pandas as pd
        
        def get_val(r_item, keys_list, default_val):
            for key in keys_list:
                val = r_item.get(key)
                if val is not None and not pd.isna(val):
                    return val
            return default_val

        for idx, row in df.iterrows():
            # Get values with robust column name mappings
            # 1. Demand Mapping
            demand = get_val(row, ["number_of_products_sold", "products_sold", "order_quantity", "demand", "Number of products sold", "Number of Products Sold", "Demand"], 1000.0)

            # 2. Inventory Mapping
            inventory = get_val(row, ["stock_levels", "inventory", "availability", "Stock levels", "Stock Levels", "Inventory"], 500.0)

            # 3. Defect/Risk Mapping
            defect_rate = get_val(row, ["defect_rates", "defect_rate", "Defect rates", "Defect Rates", "Defect Rate"], 0.0)
            # Normalize defect rate if it's high (percentage e.g. 1.5% vs decimal 0.015)
            s_risk = defect_rate / 100.0 if defect_rate > 1.0 else defect_rate

            # 4. Lead Time and OTD
            lead_time = get_val(row, ["lead_time", "lead_times", "Lead time", "Lead Time", "Lead Times"], 10)
            # Calculate an OTD score based on lead time (longer lead time = lower OTD)
            otd = 1.0 - (lead_time / 30.0)
            otd = max(0.5, min(1.0, otd))

            # 5. Financials
            cost = get_val(row, ["costs", "cost", "manufacturing_cost", "Costs", "Cost"], 50.0)
            revenue = get_val(row, ["revenue_generated", "revenue", "Revenue generated", "Revenue Generated", "Revenue"], 100.0)

            metrics.append({
                "day": int(idx),
                "demand": float(demand),
                "inventory": float(inventory),
                "supplier_risk": float(s_risk),
                "on_time_delivery": float(otd),
                "cost": float(cost),
                "revenue": float(revenue),
                "stockout": bool(inventory < demand),
                "demand_baseline": float(demand),
                "demand_trend": 0.0,
                "demand_seasonality": 0.0,
                "demand_noise": 0.0,
                "demand_spike": 0.0,
            })

        return metrics

    def compile_csv_simulation_result(self, owner_id: str = "guest", dataset_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Compile simulation-like result from the latest uploaded CSV metrics."""
        metrics = self.get_latest_metrics_from_csv(owner_id, dataset_name)
        if not metrics:
            return None

        import pandas as pd
        df = pd.DataFrame(metrics)

        # Calculate statistics
        avg_demand = float(round(df["demand"].mean(), 2)) if "demand" in df else 0.0
        max_demand = float(round(df["demand"].max(), 2)) if "demand" in df else 0.0
        avg_inventory = float(round(df["inventory"].mean(), 2)) if "inventory" in df else 0.0
        min_inventory = float(round(df["inventory"].min(), 2)) if "inventory" in df else 0.0
        avg_supplier_risk = float(round(df["supplier_risk"].mean(), 3)) if "supplier_risk" in df else 0.0
        max_supplier_risk = float(round(df["supplier_risk"].max(), 3)) if "supplier_risk" in df else 0.0
        avg_on_time = float(round(df["on_time_delivery"].mean(), 3)) if "on_time_delivery" in df else 1.0
        min_on_time = float(round(df["on_time_delivery"].min(), 3)) if "on_time_delivery" in df else 1.0
        total_cost = float(round(df["cost"].sum(), 2)) if "cost" in df else 0.0
        total_revenue = float(round(df["revenue"].sum(), 2)) if "revenue" in df else 0.0
        profit = float(round(total_revenue - total_cost, 2))
        stockout_days = int(df["stockout"].sum()) if "stockout" in df else 0
        stockout_rate = float(round(df["stockout"].mean() * 100, 1)) if "stockout" in df else 0.0

        return {
            "status": "completed",
            "days": len(df),
            "disruptions": [],
            "disruption_count": 0,
            "metrics": metrics,
            "statistics": {
                "avg_demand": avg_demand,
                "max_demand": max_demand,
                "avg_inventory": avg_inventory,
                "min_inventory": min_inventory,
                "avg_supplier_risk": avg_supplier_risk,
                "max_supplier_risk": max_supplier_risk,
                "avg_on_time": avg_on_time,
                "min_on_time": min_on_time,
                "total_cost": total_cost,
                "total_revenue": total_revenue,
                "profit": profit,
                "stockout_days": stockout_days,
                "stockout_rate": stockout_rate,
            }
        }

    async def load_user_datasets_from_db(self, owner_id: str):
        """Load datasets from MongoDB into memory for this owner if they aren't loaded."""
        state = self._get_user_state(owner_id)
        if state["current_datasets"]:
            return

        from app.core.mongodb import mongodb
        if mongodb.db is not None:
            try:
                import pandas as pd
                cursor = mongodb.db["datasets"].find({"owner_id": owner_id})
                async for doc in cursor:
                    dataset_name = doc["dataset_name"]
                    raw_data = doc["data"]
                    
                    # Convert back to DataFrame if it was a record list
                    if isinstance(raw_data, list):
                        data = pd.DataFrame(raw_data)
                    elif isinstance(raw_data, dict):
                        # Might be dict of DataFrames or dict
                        data = {}
                        for k, v in raw_data.items():
                            if isinstance(v, list):
                                data[k] = pd.DataFrame(v)
                            else:
                                data[k] = v
                    else:
                        data = raw_data
                        
                    state["current_datasets"][dataset_name] = data
                    state["data_cache"][dataset_name] = {
                        "source": doc.get("source", "csv"),
                        "timestamp": doc.get("timestamp", datetime.now().isoformat()),
                        "rows": len(raw_data) if hasattr(raw_data, "__len__") else 0,
                    }
                logger.info(f"Loaded datasets from MongoDB for owner {owner_id}")
            except Exception as e:
                logger.error(f"Failed to load datasets from MongoDB for owner {owner_id}: {e}")

    async def _save_dataset_to_db(self, dataset_name: str, data: Any, source_type: str, owner_id: str):
        """Helper to save a dataset to the MongoDB 'datasets' collection."""
        from app.core.mongodb import mongodb
        if mongodb.db is not None:
            try:
                import pandas as pd
                serializable_data = None
                if isinstance(data, pd.DataFrame):
                    serializable_data = data.to_dict(orient="records")
                elif isinstance(data, dict):
                    serializable_data = {k: (v.to_dict(orient="records") if isinstance(v, pd.DataFrame) else v) for k, v in data.items()}
                else:
                    serializable_data = data

                await mongodb.db["datasets"].update_one(
                    {"dataset_name": dataset_name, "owner_id": owner_id},
                    {
                        "$set": {
                            "dataset_name": dataset_name,
                            "owner_id": owner_id,
                            "source": source_type,
                            "timestamp": datetime.now().isoformat(),
                            "data": serializable_data
                        }
                    },
                    upsert=True
                )
                logger.info(f"Saved dataset '{dataset_name}' (owner: {owner_id}) to MongoDB.")
            except Exception as db_err:
                logger.error(f"Failed to save dataset '{dataset_name}' to MongoDB: {db_err}")

    async def delete_dataset(self, dataset_name: str, owner_id: str = "guest") -> bool:
        """Delete a dataset from memory and MongoDB Atlas."""
        state = self._get_user_state(owner_id)
        
        # Remove from in-memory caches
        if dataset_name in state["current_datasets"]:
            del state["current_datasets"][dataset_name]
        if dataset_name in state["data_cache"]:
            del state["data_cache"][dataset_name]
            
        # Clear manual buffer if it is inside the manual ingester
        if DataSourceType.MANUAL in state["data_sources"]:
            ingester = state["data_sources"][DataSourceType.MANUAL]
            ingester.clear_buffer(dataset_name)

        # Delete corresponding simulation states from memory cache
        try:
            from app.simulation.state_manager import state_manager
            keys_to_delete = [
                sid for sid, entry in state_manager.saved_states.items()
                if entry.get("owner_id") == owner_id and (
                    entry.get("label") == f"CSV: {dataset_name}" or
                    entry.get("label") == f"CSV: {dataset_name}.csv" or
                    entry.get("label") == f"CSV: {dataset_name} (updated)"
                )
            ]
            for sid in keys_to_delete:
                del state_manager.saved_states[sid]
                state_manager.state_history = [
                    s for s in state_manager.state_history if s["simulation_id"] != sid
                ]
        except Exception as e:
            logger.error(f"Failed to clear simulation states from memory for dataset {dataset_name}: {e}")

        # Delete from MongoDB collections
        from app.core.mongodb import mongodb
        if mongodb.db is not None:
            try:
                # Delete from 'datasets'
                await mongodb.db["datasets"].delete_one({"dataset_name": dataset_name, "owner_id": owner_id})
                # Delete from 'manual_buffers'
                await mongodb.db["manual_buffers"].delete_one({"dataset_name": dataset_name})
                # Delete matching simulation states
                await mongodb.db["simulations"].delete_many({
                    "owner_id": owner_id,
                    "label": {
                        "$in": [
                            f"CSV: {dataset_name}",
                            f"CSV: {dataset_name}.csv",
                            f"CSV: {dataset_name} (updated)"
                        ]
                    }
                })
                logger.info(f"Deleted dataset '{dataset_name}' and its associated simulations (owner: {owner_id}) from MongoDB.")
                return True
            except Exception as e:
                logger.error(f"Failed to delete dataset '{dataset_name}' from MongoDB: {e}")
                return False
        return True

    async def add_row_to_dataset(self, dataset_name: str, row: Dict[str, Any], owner_id: str = "guest") -> Dict[str, Any]:
        """Add a row/record to a dataset (either manual or CSV) and sync to MongoDB Atlas."""
        state = self._get_user_state(owner_id)
        
        # Ensure manual data source is initialized if we need to use it
        if DataSourceType.MANUAL not in state["data_sources"]:
            await self.initialize_data_source(DataSourceType.MANUAL, owner_id)
            
        manual_ingester = state["data_sources"][DataSourceType.MANUAL]
        
        source_type = DataSourceType.CSV.value
        
        # If the dataset is manual, or doesn't exist yet, we add it to manual buffers
        if dataset_name not in state["current_datasets"] or dataset_name in manual_ingester.data_buffer:
            source_type = DataSourceType.MANUAL.value
            # Add to manual buffer and MongoDB manual_buffers
            result = await manual_ingester.add_record(dataset_name, row)
            # Ingest manual buffer into a DataFrame for active use
            df = await manual_ingester.ingest(dataset_name)
            state["current_datasets"][dataset_name] = df
            state["data_cache"][dataset_name] = {
                "source": DataSourceType.MANUAL.value,
                "timestamp": datetime.now().isoformat(),
                "rows": len(df),
            }
            # Also save to the main 'datasets' collection in Atlas for querying
            await self._save_dataset_to_db(dataset_name, df, DataSourceType.MANUAL.value, owner_id)
        else:
            # It's an existing dataset, likely loaded via CSV
            df = state["current_datasets"][dataset_name]
            import pandas as pd
            
            # Default ID and timestamp
            row.setdefault("id", len(df) + 1)
            row.setdefault("timestamp", datetime.now().isoformat())
            
            # Prioritized mapping lists (including all casing/spacing variants)
            mapping_priorities = {
                "products_sold": [
                    "number_of_products_sold", "products_sold", "order_quantity", "demand",
                    "Number of products sold", "Number of Products Sold", "Demand", "Order quantities", "Order Quantities"
                ],
                "inventory": [
                    "stock_levels", "inventory", "availability", 
                    "Stock levels", "Stock Levels", "Inventory"
                ],
                "defect_rate": [
                    "defect_rates", "defect_rate", 
                    "Defect rates", "Defect Rates", "Defect Rate"
                ],
                "lead_time": [
                    "lead_time", "lead_times", 
                    "Lead time", "Lead Time", "Lead Times"
                ],
                "cost": [
                    "costs", "cost", "manufacturing_cost", 
                    "Costs", "Cost", "Manufacturing costs", "Manufacturing Costs", "Manufacturing cost", "Manufacturing Cost"
                ],
                "revenue": [
                    "revenue_generated", "revenue", 
                    "Revenue generated", "Revenue Generated", "Revenue"
                ]
            }
            
            mapped_row = {}
            for key, val in row.items():
                mapped = False
                if key in mapping_priorities:
                    # Look for the first column in df that matches any of the prioritized names case-insensitively and space-insensitively
                    for prioritized_name in mapping_priorities[key]:
                        p_clean = str(prioritized_name).strip().lower().replace("_", " ").replace("-", " ")
                        for col in df.columns:
                            col_clean = str(col).strip().lower().replace("_", " ").replace("-", " ")
                            if col_clean == p_clean:
                                mapped_row[col] = val
                                mapped = True
                                break
                        if mapped:
                            break
                if not mapped:
                    mapped_row[key] = val
            
            # Append new row DataFrame
            new_row_df = pd.DataFrame([mapped_row])
            updated_df = pd.concat([df, new_row_df], ignore_index=True)
            
            # Update cache and memory state
            state["current_datasets"][dataset_name] = updated_df
            state["data_cache"][dataset_name]["rows"] = len(updated_df)
            state["data_cache"][dataset_name]["timestamp"] = datetime.now().isoformat()
            
            source_type = state["data_cache"][dataset_name].get("source", DataSourceType.CSV.value)
            # Save the updated dataset to 'datasets' collection in Atlas
            await self._save_dataset_to_db(dataset_name, updated_df, source_type, owner_id)
            
        # Re-compile and save the simulation state so the dashboard updates (for both CSV and manual)
        compiled = self.compile_csv_simulation_result(owner_id, dataset_name=dataset_name)
        if compiled:
            from app.simulation.state_manager import state_manager
            from app.agents.orchestrator import get_agent_orchestrator
            import uuid
            
            env = {"metrics": compiled["metrics"], "disruptions": []}
            orchestrator = get_agent_orchestrator(owner_id)
            agent_result = await orchestrator.run_all_agents(env)
            compiled["agent_analysis"] = agent_result.get("summary", {})
            
            sim_id = f"csv-{str(uuid.uuid4())[:8]}"
            label_suffix = "(updated)" if source_type == DataSourceType.CSV.value else "(manual)"
            await state_manager.save_state(sim_id, compiled, label=f"CSV: {dataset_name} {label_suffix}", owner_id=owner_id)
            compiled["simulation_id"] = sim_id
            
        return {
            "status": "success",
            "dataset_name": dataset_name,
            "rows": len(state["current_datasets"][dataset_name]),
            "source": source_type
        }

    async def merge_datasets(self, dataset_names: List[str], merged_name: str, owner_id: str = "guest") -> Dict[str, Any]:
        """Merge multiple datasets chronologically and run agent analysis."""
        state = self._get_user_state(owner_id)
        
        # Load and verify all target datasets
        dfs = []
        for name in dataset_names:
            if name not in state["current_datasets"]:
                raise ValueError(f"Dataset '{name}' not found")
            df = state["current_datasets"][name]
            import pandas as pd
            if not isinstance(df, pd.DataFrame):
                raise ValueError(f"Dataset '{name}' cannot be merged (invalid format)")
            dfs.append(df)
            
        import pandas as pd
        # Concatenate DataFrames chronologically (consecutive index)
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Update cache and memory state
        state["current_datasets"][merged_name] = merged_df
        state["data_cache"][merged_name] = {
            "source": "merged",
            "timestamp": datetime.now().isoformat(),
            "rows": len(merged_df),
        }
        
        # Save merged dataset to MongoDB
        await self._save_dataset_to_db(merged_name, merged_df, "merged", owner_id)
        
        # Compile simulation and run agent coordination
        compiled = self.compile_csv_simulation_result(owner_id, dataset_name=merged_name)
        if compiled:
            from app.simulation.state_manager import state_manager
            from app.agents.orchestrator import get_agent_orchestrator
            import uuid
            
            env = {"metrics": compiled["metrics"], "disruptions": []}
            orchestrator = get_agent_orchestrator(owner_id)
            agent_result = await orchestrator.run_all_agents(env)
            compiled["agent_analysis"] = agent_result.get("summary", {})
            
            sim_id = f"csv-{str(uuid.uuid4())[:8]}"
            await state_manager.save_state(sim_id, compiled, label=f"CSV: {merged_name} (merged)", owner_id=owner_id)
            compiled["simulation_id"] = sim_id
            return compiled
            
        return {
            "status": "success",
            "dataset_name": merged_name,
            "rows": len(merged_df),
            "source": "merged"
        }


# Global data manager instance
data_manager = DataManager()
