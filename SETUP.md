# Setup & Installation Guide

This document describes how to set up, run, and test the Agentic Supply Chain Orchestrator.

---

## 📋 Prerequisites

*   **Python 3.11+** (Python 3.13 recommended)
*   **Node.js 18+** (Node.js 20 LTS recommended)
*   **Docker & Docker Compose** (Optional, for containerized execution)

---

## 🛠️ Local Development Setup

### 1. Backend Setup

Initialize the virtual environment, install requirements, and run the FastAPI server:

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```

The API docs will be interactive and available at `http://localhost:8000/docs`.

### 2. Frontend Setup

Install Node packages and launch the Vite dev server:

```bash
cd frontend

# Install Node modules
npm install

# Run the Vite dev server
npm run dev
```

Open your browser and navigate to `http://localhost:5173`.

---

## ⚙️ Environment Variables

Create a `.env` file in the `backend/` directory to configure the application. Here is a baseline configuration:

```env
APP_MODE=simulation
DATA_SOURCE=manual
SIMULATION_ENABLED=true
SIMULATION_SPEED=1.0
DATABASE_URL=sqlite+aiosqlite:///./data/supply_chain.db
REDIS_ENABLED=false
USE_LLM_AGENTS=false
DEBUG=true
```

To run with **OpenAI LLM Agents**:
```env
USE_LLM_AGENTS=true
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo
```

---

## 🧪 Testing

Run backend tests using pytest from the `backend` directory:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

This will run basic unit tests and end-to-end simulation cycle tests.
