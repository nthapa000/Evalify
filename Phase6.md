# Phase 6 — Docker Containerisation

## Overview

Phase 6 wraps every Evalify service in a Docker container so the full stack
can be started with a single command. Ollama continues to run on the host
(GPU access) and the backend container reaches it over the Docker host-gateway.

---

## Architecture

```
Host Machine
├── Ollama (GPU)           localhost:11434    (runs outside Docker, needs GPU)
│
└── Docker Compose (evalify-net bridge network)
    ├── mongodb            localhost:27017    mongo:7
    ├── mlflow             localhost:5005     python:3.11-slim + mlflow 2.13.0
    ├── backend            localhost:47823    evalify-backend:dev  (FastAPI)
    └── frontend           localhost:5173     evalify-frontend:dev (nginx + React)
```

### Request flow (browser → frontend → backend → Ollama)

```
Browser
  → http://localhost:5173/api/papers
  → nginx (frontend container) proxies /api/* → http://backend:8000
  → FastAPI (backend container)
  → Ollama on host (http://host.docker.internal:11434)  [GPU]
  → MongoDB (mongodb container)
  → MLflow (mlflow container)
```

---

## Service URLs

| Service      | URL                           | Notes                          |
|--------------|-------------------------------|--------------------------------|
| Frontend     | http://localhost:5173         | React SPA                      |
| Backend API  | http://localhost:47823        | FastAPI (direct, for debugging)|
| API Docs     | http://localhost:47823/docs   | Swagger UI                     |
| MLflow UI    | http://localhost:5005         | Experiment tracking            |
| MongoDB      | localhost:27017               | Internal only                  |
| Ollama       | http://localhost:11434        | On host (GPU)                  |

---

## Files Changed / Added

| File | Change |
|---|---|
| `backend/Dockerfile` | Added system libs (OpenCV, EasyOCR), health check, env defaults |
| `backend/.dockerignore` | Excludes venv, uploads, logs, tests |
| `frontend/nginx.conf` | Added `/api/` reverse proxy to backend container |
| `frontend/.dockerignore` | Excludes node_modules, dist |
| `backend/app/main.py` | CORS origins now read from `CORS_ORIGINS` env var |
| `docker-compose.dev.yml` | Full rewrite — now includes backend + frontend services |

---

## Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose v2+
- Ollama running on host with `llama3.2-vision:11b` loaded
- Credential files present: `teacher_credentials.env`, `student_credentials.env`

### 1. Start everything

```bash
# From the Evalify/ root directory
docker compose -f docker-compose.dev.yml up -d
```

First run will:
- Pull `mongo:7` and `python:3.11-slim` images
- Build `evalify-backend:dev` (~4–6 GB, takes 5–10 min — installs torch, easyocr, etc.)
- Build `evalify-frontend:dev` (~200 MB, takes 1–2 min)

### 2. Watch startup logs

```bash
docker compose -f docker-compose.dev.yml logs -f
```

Healthy startup sequence:
```
evalify-mongo    | Ready to accept connections
evalify-mlflow   | Booting worker with pid ...
evalify-backend  | ✅ Connected to MongoDB: evalify_db
evalify-backend  | ✅ Ollama: 'llama3.2-vision:11b' ready at http://host.docker.internal:11434
evalify-backend  | Application startup complete.
evalify-frontend | nginx: ready to serve
```

### 3. Verify all services are healthy

```bash
docker compose -f docker-compose.dev.yml ps
```

All four services should show `healthy` or `running`.

### 4. Open the app

| What | URL |
|---|---|
| App | http://localhost:5173 |
| API health | http://localhost:47823/api/health |
| API docs | http://localhost:47823/docs |
| MLflow | http://localhost:5005 |

---

## Common Commands

```bash
# Rebuild only the backend image (after code changes)
docker compose -f docker-compose.dev.yml up --build -d backend

# Rebuild only the frontend image
docker compose -f docker-compose.dev.yml up --build -d frontend

# View logs for one service
docker compose -f docker-compose.dev.yml logs -f backend

# Stop all services (data is preserved in volumes)
docker compose -f docker-compose.dev.yml down

# Stop and wipe all data (full reset)
docker compose -f docker-compose.dev.yml down -v

# Open a shell inside the backend container
docker exec -it evalify-backend bash

# Check Ollama connectivity from inside the backend container
docker exec evalify-backend curl -s http://host.docker.internal:11434/api/tags | head -c 200
```

---

## Environment Variables

All backend config is passed via `docker-compose.dev.yml` environment + env_file.

| Variable | Default in Docker | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://evalify:...@mongodb:27017/...` | MongoDB connection |
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000` | MLflow server (internal port) |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama on host machine |
| `OLLAMA_TIMEOUT` | `300` | Vision call timeout (seconds) |
| `OLLAMA_TIMEOUT_SUBJECTIVE` | `180` | Per-question fallback timeout |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost` | Allowed browser origins |

---

## Volumes

| Volume | Mount | Purpose |
|---|---|---|
| `mongo-data` | `/data/db` | MongoDB database files |
| `mlflow-data` | `/mlflow` | MLflow DB + uploaded artifacts |
| `backend-uploads` | `/app/uploads` | Student answer sheets + teacher PDFs |

Volumes survive `docker compose down` but are deleted by `docker compose down -v`.

---

## Ollama — GPU on Host

Ollama runs **outside Docker** because it needs direct GPU access.
The backend container reaches Ollama via the `host.docker.internal` hostname,
which maps to the host machine's IP through Docker's `host-gateway` alias
(set via `extra_hosts` in docker-compose).

```bash
# Confirm Ollama is reachable from inside the backend container
docker exec evalify-backend curl http://host.docker.internal:11434/api/tags
```

If Ollama is not running on the host, the backend falls back to stub mode and
prints `⚠️ Ollama: did not start — handwritten OCR will run in STUB mode`.

---

## Troubleshooting

### Backend container exits immediately
```bash
docker logs evalify-backend
```
Common causes:
- MongoDB not yet healthy — backend waits but may time out. Run `docker compose up -d mongodb` first, wait for healthy, then `docker compose up -d backend`.
- `teacher_credentials.env` or `student_credentials.env` missing from project root.

### Frontend shows blank page / API errors
```bash
# Check nginx is proxying correctly
docker exec evalify-frontend curl http://backend:8000/api/health
```
If that fails, the `evalify-net` network may not have DNS for `backend`. Ensure both containers are in `evalify-net`.

### Ollama not reachable from backend
```bash
docker exec evalify-backend curl http://host.docker.internal:11434/api/tags
```
If this fails, check that Ollama is running on the host (`curl http://localhost:11434/api/tags`). The `extra_hosts: host.docker.internal:host-gateway` line in docker-compose handles the Linux host-gateway mapping.

### Port already in use
```bash
# Find what's using port 5173
lsof -i :5173
# Or change the host port in docker-compose.dev.yml, e.g. "5174:80"
```

### Backend image build too slow / out of disk space
The `evalify-backend:dev` image is ~4–6 GB (torch + easyocr). If disk space is tight:
```bash
docker system prune -f        # remove dangling images/containers
docker image prune -a -f      # remove all unused images
```

---

## What Was NOT Containerised

| Component | Reason |
|---|---|
| **Ollama** | Needs direct GPU (CUDA) access; cannot easily pass through Docker without `nvidia-container-toolkit` AND the host already runs it reliably |

To fully containerise Ollama (optional, requires `nvidia-container-toolkit`):
```yaml
ollama:
  image: ollama/ollama
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
  ports:
    - "11434:11434"
  volumes:
    - ollama-models:/root/.ollama
```
Then set `OLLAMA_HOST: http://ollama:11434` in the backend service.
