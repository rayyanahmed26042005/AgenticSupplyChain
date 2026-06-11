# Agentic Supply Chain Orchestrator

An AI-powered autonomous supply chain management and orchestration platform. It models complex supply chains with real-time analytics, demand forecasting, risk prediction, and automated decisions executed by cooperating agents.

---

## 🚀 Key Features

*   **Multi-Mode Operations**: Switch seamlessly between **Simulation**, **Real-Time**, and **Hybrid** execution models.
*   **Autonomous Cooperating Agents**: Managed by an orchestrator, agents handle specialized roles:
    *   **Demand Agent**: Learns ordering thresholds, safety stock buffer rules, and manages forecasts.
    *   **Supplier Risk Agent**: Monitors on-time delivery, defect rates, and supplier profiles to compute risk.
    *   **Coordinator Agent**: Resolves inventory-replenishment conflicts between agents and schedules optimal operations.
*   **Machine Learning Analytics**: Time-series demand forecasting with confidence intervals and supplier risk prediction.
*   **Extensive Event Engine**: Priority queue event bus orchestrating asynchronous actions and disruptions.
*   **Interactive Simulation Dashboard**: Sleek glassmorphism React-TS dashboard with Recharts visualizations, scenario triggers, and disruption simulators.

---

## 🛠️ Stack & Architecture

### Backend
*   **Framework**: FastAPI (Python 3.13)
*   **Database**: SQLite/PostgreSQL (SQLAlchemy async)
*   **Data Science & ML**: Pandas, NumPy, Scikit-Learn
*   **Event Broker**: In-process Priority Event Bus
*   **Task Runners**: Asyncio

### Frontend
*   **Framework**: React (TypeScript, Vite)
*   **State Management**: Zustand
*   **Visualizations**: Recharts
*   **Aesthetics**: Vanilla CSS with customized dark glassmorphism theme

---

## ⚡ Quick Start

### 1. Install & Build
Detailed instructions can be found in [SETUP.md](file:///c:/Users/ahmed/Desktop/supply%20chain/SETUP.md).

```bash
# Run backend server
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Run frontend dev server
cd ../frontend
npm install
npm run dev
```

### 2. Docker Compose
Run the entire platform with a single command:
```bash
docker-compose up --build
```
Access the dashboard at `http://localhost` and the API documentation at `http://localhost:8000/docs`.

---

## 📖 Mode Guide
Learn how to leverage different environments (Simulation vs. Real-Time streaming) in [MODE_GUIDE.md](file:///c:/Users/ahmed/Desktop/supply%20chain/MODE_GUIDE.md).
