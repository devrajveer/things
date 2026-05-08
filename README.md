# MegaIoT Platform

MegaIoT is a high-performance, multi-tenant Internet of Things (IoT) platform built for scale. It handles device provisioning, real-time telemetry ingestion, streaming analytics, rules-based automation, and fleet OTA management.

## System Architecture

The platform uses a microservices architecture to separate concerns and scale horizontally.

```mermaid
graph TD
    subgraph Edge
        D[IoT Devices]
    end

    subgraph "Ingest Layer"
        IA[Ingest API (FastAPI)]
        MB[NATS JetStream]
    end

    subgraph "Processing Layer"
        W_D[Decoder Worker]
        W_W[DB Writer Worker]
        W_R[Rules Engine]
        W_O[OTA Manager]
        W_A[Action Dispatcher]
    end

    subgraph "Storage Layer"
        DB[(PostgreSQL / TimescaleDB)]
        REDIS[(Redis State Cache)]
    end

    subgraph "Application Layer"
        CA[Core API (FastAPI)]
        RT[Real-time SSE (Node.js)]
        WEB[Web Dashboard (Next.js)]
    end

    D -- "Telemetry (MQTT/HTTP)" --> IA
    IA -- "telemetry.raw.v1" --> MB
    
    MB -- "Consume" --> W_D
    W_D -- "telemetry.datapoint.v1" --> MB
    
    MB -- "Consume" --> W_W
    W_W -- "Write" --> DB
    
    MB -- "Consume" --> W_R
    W_R -- "Check State" --> REDIS
    W_R -- "action.webhook.v1" --> MB
    
    MB -- "Consume" --> W_A
    W_A -- "Trigger" --> Webhooks[External Webhooks]
    
    MB -- "Consume" --> RT
    RT -- "Server-Sent Events" --> WEB
    
    WEB -- "REST (CRUD)" --> CA
    CA -- "Manage" --> DB
```

## Core Components

1. **Core API (`services/api`)**: FastAPI application managing Organizations, Projects, Devices, Dashboards, and Rules.
2. **Ingest Service (`services/ingest`)**: High-throughput FastAPI service strictly for receiving device telemetry and publishing to NATS.
3. **Background Worker (`services/worker`)**: Python service running asynchronous NATS consumers (Decoding, DB Writing, Rule Evaluation, OTA).
4. **Real-time Service (`services/realtime`)**: Node.js service providing Server-Sent Events (SSE) to stream live data to the UI.
5. **Web Dashboard (`apps/web`)**: Next.js React application with a premium glassmorphic UI, featuring a drag-and-drop dashboard builder.

## Prerequisites & Setup

You will need the following infrastructure:
1. **PostgreSQL** (with TimescaleDB extension)
2. **Redis**
3. **NATS JetStream**

### Quick Start (Local Development)

1. **Install Dependencies**:
    The project uses NPM for the frontend monorepo and standard Python environments for the backend.
    ```bash
    npm install
    ```

2. **Configure Environment Variables**:
    Ensure the `.env` file at the root contains the required connection strings:
    ```env
    POSTGRES_DSN=postgresql+asyncpg://user:pass@host:5432/dbname
    REDIS_URL=redis://host:6379/0
    NATS_URL=nats://localhost:4222
    JWT_SECRET=your_super_secret_key
    ```

3. **Start the Infrastructure** (if using local Docker):
    ```bash
    docker run -d --name nats-main -p 4222:4222 -p 8222:8222 nats -js
    ```

4. **Run the Application**:
    You can run each service individually or use a script. See `scripts/start-dev.ps1` (if available) to boot the entire stack at once.

    To run the web interface:
    ```bash
    npm run dev --workspace=web
    ```

## Simulating Data

Once the platform is running, you can use the simulation script to test the ingestion pipeline:
```bash
python scripts/simulate_device.py
```
This script will authenticate via the HTTP ingest endpoint and send randomized temperature and humidity data.
