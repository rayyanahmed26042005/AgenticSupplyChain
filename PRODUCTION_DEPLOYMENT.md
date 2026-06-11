# Production Deployment Guide

This document describes how to deploy the Agentic Supply Chain Orchestrator application to a production environment using Docker, Nginx, and environmental configurations.

---

## Architecture Overview

In a production environment, the application is divided into two decoupled layers served behind a single entry point:

1.  **Frontend (Web Client)**: Built into optimized static HTML/JS/CSS assets and served via Nginx on port `80`.
2.  **Backend (API Server)**: Running on FastAPI (`uvicorn`) on port `8000`.
3.  **Reverse Proxy (Nginx)**: Fronts the setup. It intercepts any incoming requests:
    *   Requests to `/api` are reverse-proxied directly to the Backend API.
    *   All other requests route to the static frontend build.
    *   This eliminates the need for CORS setup and avoids hardcoding host ports/domains in the client code.

---

## 1. Local Production Simulation (Docker Compose)

To verify the production build locally before pushing to cloud providers:

1.  Copy the production environment template to `.env`:
    ```bash
    cp .env.production.example .env
    ```
2.  Customize database connections, MongoDB URI, and API keys.
3.  Build and launch the containers:
    ```bash
    docker-compose up --build -d
    ```
4.  Access the UI at `http://localhost`. All backend queries are routed through `/api/v1` automatically.

---

## 2. Production Environment Checklist

Ensure the following variables in `.env` are configured for production:

*   `ENVIRONMENT=production`: Disables debug modes and API reloads.
*   `DATABASE_URL`: Set to a robust cloud database connection (e.g., AWS RDS PostgreSQL).
*   `REDIS_URL` / `REDIS_ENABLED=true`: Configured to connect to a Redis cache cluster (e.g., AWS ElastiCache).
*   `MONGODB_URI`: Points to your production MongoDB Atlas cluster for dataset storage and simulation replay.
*   `JWT_SECRET`: Changed from development default to a high-entropy secret string.
*   `CORS_ORIGINS`: Set to your explicit domain name (e.g., `["https://app.yourcompany.com"]`) to enforce CORS security.

---

## 3. General Cloud Deployment Strategy (AWS, GCP, Azure)

For production deployment in a cloud container service (like **Amazon ECS Fargate** or **Google Cloud Run**):

### Step A: Build and Push Docker Images
Build the container images from the root directory and push them to a container registry (e.g., Amazon ECR or Google Artifact Registry):

```bash
# 1. Build backend image
docker build -t supply-chain-backend:latest -f docker/Dockerfile.backend .

# 2. Build frontend image
docker build -t supply-chain-frontend:latest -f docker/Dockerfile.frontend .

# 3. Tag and push to ECR (AWS example)
docker tag supply-chain-backend:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/supply-chain-backend:latest
docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/supply-chain-backend:latest

docker tag supply-chain-frontend:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/supply-chain-frontend:latest
docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/supply-chain-frontend:latest
```

### Step B: Provision Managed Services
*   **Database**: Provision a managed PostgreSQL instance (e.g., AWS RDS). Run migration scripts on initialization.
*   **Cache**: Provision a managed Redis cluster (e.g., AWS ElastiCache Redis).
*   **NoSQL Storage**: Utilize a MongoDB Atlas cluster. Ensure network access (IP whitelisting / VPC peering) is enabled.

### Step C: Deploy Containers
1.  **Task Definitions / Task Groups**:
    *   Define a task group running both the `frontend` container (port 80) and the `backend` container (port 8000).
    *   Set the `backend` environment variables (e.g., `DATABASE_URL`, `MONGODB_URI`, `REDIS_URL`) using secret managers (like AWS Secrets Manager or Parameter Store).
2.  **Load Balancer**:
    *   Configure an Application Load Balancer (ALB) to expose the frontend Nginx container (port 80) to public traffic.
    *   Redirect HTTP to HTTPS at the load balancer level.
