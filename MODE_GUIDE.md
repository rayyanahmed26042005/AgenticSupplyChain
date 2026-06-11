# Application Mode Guide

The Agentic Supply Chain Orchestrator is designed to work across multiple operational modes to accommodate sandboxed testing (simulation) as well as production-ready pipelines (real-time stream processing).

---

## 🎛️ App Modes Overview

### 1. Simulation Mode
*   **Purpose**: Sandbox testing, policy verification, agent learning, stress-testing.
*   **Behavior**: Generates realistic daily metrics (demand cycles, seasonal spikes, holding costs, on-time delivery percentages) based on mathematical formulations and configurable seeds.
*   **Agent Interaction**: Agents run synchronously at the end of each simulation step to determine restocking thresholds and mitigate supplier risks.

### 2. Real-Time Mode
*   **Purpose**: Production deployments connected to streaming pipelines.
*   **Behavior**: Reads metrics directly from connected data brokers (Kafka, API polling, database queries, manual inserts).
*   **Agent Interaction**: Agents run asynchronously reacting to events on the in-process event bus (e.g. `DemandEvent`, `SupplyEvent`).

### 3. Hybrid Mode
*   **Purpose**: Combines historical base metrics with real-time feedback loops.
*   **Behavior**: Reads historical data as the baseline, overlaying active real-time events to dynamically update metrics.

---

## 📥 Ingestion & Validation

Every data source undergoes validation through the ingestion schema checks:

1.  **Normalization**: Aligning fields like `OTD`, `inventory_count`, and `sales` to standard schemas.
2.  **Schema Check**: Pydantic schema validation for records.
3.  **Risk Profiling**: Automatic calculations of defect and delayed arrival rates to supply immediate risk signals to the agent network.
