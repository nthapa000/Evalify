# Phase 6 — Docker Containerisation

## Overview

Phase 6 wraps every Evalify service in a Docker container so the full stack can be started with a single command. Ollama continues to run on the **host** (needs direct GPU access) and the backend container reaches it via the Docker host-gateway bridge.

---

## Architecture

```
Host Machine
├── Ollama  (GPU — runs outside Docker, needs CUDA)    localhost:11434
│
└── Docker Compose  (bridge network: evalify_evalify-net, subnet 172.18.0.0/16)
    ├── evalify-mongo      172.18.0.3   mongo:7                 → localhost:27017
    ├── evalify-mlflow     172.18.0.2   ghcr.io/mlflow/mlflow   → localhost:5005
    ├── evalify-backend    172.18.0.4   evalify-backend:dev     → localhost:47823
    └── evalify-frontend   172.18.0.5   evalify-frontend:dev    → localhost:5173
```

### Request Flow (browser → nginx → FastAPI → Ollama/MongoDB)

```
Browser
  → http://localhost:5173/api/papers
  → nginx (evalify-frontend container)
      resolver 127.0.0.11  (Docker embedded DNS)
      proxy_pass http://backend:8000
  → FastAPI (evalify-backend container)
      connects to: mongodb:27017   (evalify-mongo container)
                   mlflow:5000     (evalify-mlflow container)
                   host.docker.internal:11434  (Ollama on host with GPU)
```

### Port Map

| Service | Container Port | Host Port | Access URL |
|---|---|---|---|
| MongoDB | 27017 | 27017 | `localhost:27017` |
| MLflow | 5000 | 5005 | `http://localhost:5005` |
| FastAPI Backend | 8000 | 47823 | `http://localhost:47823` |
| React Frontend (nginx) | 80 | 5173 | `http://localhost:5173` |
| Ollama (host) | 11434 | 11434 | `http://localhost:11434` |

---

## Files Changed / Added

| File | What Changed |
|---|---|
| `backend/Dockerfile` | Added system libs (OpenCV, EasyOCR), health check, env defaults |
| `backend/.dockerignore` | Excludes venv/, uploads/, logs, tests |
| `backend/app/main.py` | CORS configurable via `CORS_ORIGINS` env var; venv warning skipped in Docker |
| `backend/app/db/mongodb.py` | Connection retries (10× with 5s delay) for Docker startup timing |
| `frontend/Dockerfile` | Multi-stage build: Node build → nginx:alpine serve |
| `frontend/nginx.conf` | `/api/` reverse proxy to backend; lazy DNS via `resolver 127.0.0.11` |
| `frontend/.dockerignore` | Excludes node_modules/, dist/ |
| `docker-compose.dev.yml` | Full rewrite — all 4 services, named network, named volumes |
| `backend/db/mongo-init.js` | Init script creates collections, indexes, placeholder seed users |

---

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose v2+
- Ollama running on the host with `llama3.2-vision:11b` pulled
  ```bash
  ollama pull llama3.2-vision:11b
  ollama serve   # starts Ollama API on localhost:11434
  ```
- Credential files in project root (already committed with dev values):
  - `teacher_credentials.env`
  - `student_credentials.env`

---

### 1. Start Everything (first run)

```bash
# From the Evalify/ root directory
docker compose -f docker-compose.dev.yml up -d
```

**What happens on first run:**
- Pulls `mongo:7` (~700 MB), `ghcr.io/mlflow/mlflow:v2.13.0` (~220 MB)
- Builds `evalify-backend:dev` — installs torch, easyocr, opencv (~4–6 GB, takes 10–20 min)
- Builds `evalify-frontend:dev` — npm install + vite build (~200 MB, takes 1–2 min)
- MongoDB init script creates collections and indexes
- FastAPI seeds teacher + student users with real bcrypt hashes

**Tip:** The backend image build is the bottleneck (heavy ML libraries). Subsequent starts use the cached image and take < 30 seconds.

---

### 2. Watch Startup Logs

```bash
docker compose -f docker-compose.dev.yml logs -f
```

Expected healthy startup sequence:
```
evalify-mongo    | Ready to accept connections on port 27017
evalify-mlflow   | Listening at: http://0.0.0.0:5000
evalify-backend  | ✅ Connected to MongoDB: evalify_db
evalify-backend  | 🌱 Seeded teacher: teacher@evalify.local   (or "✓ already exists")
evalify-backend  | ✅ Evaluator loaded.
evalify-backend  | Application startup complete.
evalify-frontend | nginx: worker process started
```

---

### 3. Verify All Services Are Healthy

```bash
docker compose -f docker-compose.dev.yml ps
```

Expected output (all services showing `healthy` or `Up`):
```
NAME               IMAGE                           STATUS
evalify-backend    evalify-backend:dev             Up X minutes (healthy)
evalify-frontend   evalify-frontend:dev            Up X minutes
evalify-mlflow     ghcr.io/mlflow/mlflow:v2.13.0  Up X minutes (healthy)
evalify-mongo      mongo:7                         Up X minutes (healthy)
```

---

### 4. Test Endpoints

```bash
# Backend health (direct)
curl http://localhost:47823/api/health
# → {"status":"ok","service":"evalify-backend","version":"0.2.0"}

# Frontend serving React SPA
curl -I http://localhost:5173/
# → HTTP/1.1 200 OK

# API proxied through nginx (frontend → backend)
curl http://localhost:5173/api/health
# → {"status":"ok","service":"evalify-backend","version":"0.2.0"}

# MLflow UI
curl -I http://localhost:5005/
# → HTTP/1.1 200 OK

# Teacher login
curl -X POST http://localhost:47823/api/auth/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@evalify.local","password":"Teacher@123"}'
```

---

## Service URLs

| Service | URL | Notes |
|---|---|---|
| **React Frontend** | http://localhost:5173 | Main app (teacher & student UI) |
| **Backend API** | http://localhost:47823 | FastAPI — direct access for debugging |
| **API Swagger Docs** | http://localhost:47823/docs | Interactive API documentation |
| **API ReDoc** | http://localhost:47823/redoc | Alternative docs |
| **MLflow UI** | http://localhost:5005 | ML experiment tracking |
| **MongoDB** | localhost:27017 | Internal database |
| **Ollama** | http://localhost:11434 | On host with GPU (outside Docker) |

---

## Common Commands

```bash
# Start all services (detached)
docker compose -f docker-compose.dev.yml up -d

# Rebuild + restart a specific service after code changes
docker compose -f docker-compose.dev.yml up -d --build backend
docker compose -f docker-compose.dev.yml up -d --build frontend

# Follow logs for all services
docker compose -f docker-compose.dev.yml logs -f

# Follow logs for one service
docker compose -f docker-compose.dev.yml logs -f backend

# Open a shell inside the backend container
docker exec -it evalify-backend bash

# Check MongoDB connectivity from backend
docker exec evalify-backend python3 -c "import socket; print(socket.gethostbyname('mongodb'))"

# Check Ollama connectivity from backend container
docker exec evalify-backend curl http://host.docker.internal:11434/api/tags

# Access MongoDB shell
docker exec -it evalify-mongo mongosh -u evalify -p evalify_dev_pass --authenticationDatabase admin

# Stop all services (volumes preserved)
docker compose -f docker-compose.dev.yml down

# Stop and DELETE all data (full reset)
docker compose -f docker-compose.dev.yml down -v

# Show image sizes
docker images | grep evalify
```

---

## Environment Variables

All backend configuration is passed via `docker-compose.dev.yml` environment section + `env_file`.

| Variable | Value in Docker | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://evalify:evalify_dev_pass@mongodb:27017/evalify_db?authSource=admin` | MongoDB connection (uses Docker DNS `mongodb`) |
| `MONGO_DB_NAME` | `evalify_db` | Database name |
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000` | MLflow server (internal container port 5000) |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama on host via host-gateway |
| `OLLAMA_TIMEOUT` | `300` | Vision OCR call timeout (seconds) |
| `OLLAMA_TIMEOUT_SUBJECTIVE` | `180` | Subjective grading timeout per question |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost,http://localhost:47823` | Browser origins allowed |
| `TEACHER_JWT_SECRET` | From `teacher_credentials.env` | JWT signing secret |
| `STUDENT_JWT_SECRET` | From `student_credentials.env` | JWT signing secret |

---

## Volumes

Named Docker volumes persist data across `docker compose down` restarts.
They are only deleted by `docker compose down -v`.

| Volume Name | Container Mount | Stores |
|---|---|---|
| `mongo-data` | `/data/db` | All MongoDB documents (papers, submissions, results, users) |
| `mlflow-data` | `/mlflow` | MLflow SQLite database + uploaded model artifacts |
| `backend-uploads` | `/app/uploads` | Teacher question paper PDFs + student answer sheet images |

---

## Docker Network

All services are on the **`evalify_evalify-net`** bridge network (subnet `172.18.0.0/16`).
Docker's embedded DNS resolver (`127.0.0.11`) resolves service names:
- `mongodb` → `172.18.0.3`
- `mlflow` → `172.18.0.2`
- `backend` → `172.18.0.4`

---

## Ollama — GPU on the Host

Ollama runs **outside Docker** to keep direct CUDA/GPU access. The backend container reaches it via the `host.docker.internal` hostname, which is mapped to the host's bridge gateway IP through:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This is a Linux-specific trick (on Mac/Windows, `host.docker.internal` works natively).

```bash
# Verify Ollama is reachable from inside backend
docker exec evalify-backend curl http://host.docker.internal:11434/api/tags

# If Ollama is not running, backend logs show:
# ⚠️ Ollama: did not start — handwritten OCR will run in STUB mode
```

### Optional: Fully Containerise Ollama (requires nvidia-container-toolkit)

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

---

## Key Implementation Details

### 1. MongoDB Connection Retry (`backend/app/db/mongodb.py`)

The backend uses a retry loop (10 attempts × 5 s delay = 50 s max wait) to connect to MongoDB at startup. This makes the backend resilient to:
- MongoDB being slow to initialize on first run
- Network attachment timing issues during Docker container restart cycles

```python
async def connect_db(max_retries=10, delay_s=5.0):
    for attempt in range(1, max_retries + 1):
        try:
            await _client.admin.command("ping")
            return  # success
        except ServerSelectionTimeoutError:
            await asyncio.sleep(delay_s)
```

### 2. Nginx Lazy DNS Resolution (`frontend/nginx.conf`)

nginx resolves upstream hostnames **at startup** by default. If `backend` is not yet reachable, nginx exits immediately. The fix uses Docker's embedded DNS resolver (`127.0.0.11`) with a variable proxy_pass so the hostname is resolved **per request** instead:

```nginx
resolver 127.0.0.11 valid=10s ipv6=off;

location /api/ {
    set $backend http://backend:8000;
    proxy_pass $backend;   # resolved lazily at request time
    ...
}
```

### 3. CORS Configuration (`backend/app/main.py`)

CORS origins are read from the `CORS_ORIGINS` environment variable at startup instead of being hardcoded, allowing Docker deployments to add or remove allowed origins without rebuilding the image:

```python
_cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
```

### 4. MLflow Official Image

The official `ghcr.io/mlflow/mlflow:v2.13.0` image is used instead of `python:3.11-slim + pip install`. Benefits:
- Starts in seconds (no pip install overhead)
- Binds correctly to `0.0.0.0:5000` (known issue with gunicorn 22 + python:slim)
- Pinned to the exact same version as the Python dependency

### 5. MongoDB Init Script (`backend/db/mongo-init.js`)

Runs once when the MongoDB container is first created (before the Python app starts). Creates all collections with proper indexes. The Python `seed.py` then runs at backend startup and fixes any placeholder password hashes left by the init script.

---

## Dockerfile Details

### Backend (`backend/Dockerfile`)

```
FROM python:3.11-slim
↓
apt-get: gcc g++ libffi-dev         (build tools for wheels)
         libgl1 libglib2.0-0         (OpenCV)
         libsm6 libxext6 libxrender-dev (OpenCV display)
         libgomp1                    (EasyOCR / PyTorch OpenMP)
         curl                        (healthcheck)
↓
pip install -r requirements.txt     (~4–6 GB: torch, easyocr, opencv, fastapi, motor…)
↓
COPY app/                           (FastAPI application code)
↓
EXPOSE 8000
HEALTHCHECK: curl -f /api/health
CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Image size:** ~4–6 GB (dominated by torch + easyocr)

### Frontend (`frontend/Dockerfile`)

Multi-stage build keeps the final image small:

```
Stage 1: node:20-alpine (builder)
  npm ci                 (install all dependencies)
  npm run build          (vite build → /app/dist)

Stage 2: nginx:alpine (final, ~25 MB)
  COPY dist/ → /usr/share/nginx/html
  COPY nginx.conf → /etc/nginx/conf.d/default.conf
  EXPOSE 80
```

**Image size:** ~30 MB (only nginx + compiled static assets)

---

## Startup Order and Dependencies

```
mongodb ──────────────────────────────── (no deps)
                ↓ (service_healthy)
backend ─────────────────────────────── depends on mongodb:healthy
                ↓ (service_healthy)
frontend ────────────────────────────── depends on backend:healthy

mlflow ───────────────────────────────── (no deps, starts in parallel)
```

The `service_healthy` condition ensures:
1. MongoDB must pass `mongosh --eval "db.adminCommand('ping')"` before backend starts
2. Backend must return HTTP 200 on `/api/health` before frontend starts

---

## Troubleshooting

### Backend can't connect to MongoDB

```bash
docker logs evalify-backend | grep -E "MongoDB|retry"
```

If you see `⏳ MongoDB not ready (attempt N/10)`, MongoDB is still initializing. Wait up to 50 seconds. If it fails after 10 attempts:

```bash
# Check MongoDB is healthy
docker compose -f docker-compose.dev.yml ps mongodb

# Check MongoDB logs
docker logs evalify-mongo | tail -20

# Manually test connection
docker exec evalify-backend python3 -c "import socket; print(socket.gethostbyname('mongodb'))"
```

### Backend container exits immediately (first run only)

This can happen if the container starts before its network attachment is complete (Docker daemon timing issue). Fix: remove the exited container and recreate it.

```bash
docker compose -f docker-compose.dev.yml rm -f backend
docker compose -f docker-compose.dev.yml up -d backend
```

If the issue persists, start services individually in order:

```bash
docker compose -f docker-compose.dev.yml up -d mongodb
# wait for: docker compose ps | grep "healthy"
docker compose -f docker-compose.dev.yml up -d mlflow
docker compose -f docker-compose.dev.yml up -d --no-deps backend
docker compose -f docker-compose.dev.yml up -d --no-deps frontend
```

### Frontend shows blank page or 502 Bad Gateway

nginx can't reach the backend container. Check:

```bash
# Is backend running and healthy?
docker compose -f docker-compose.dev.yml ps backend

# Can nginx resolve and reach backend?
docker exec evalify-frontend wget -qO- http://backend:8000/api/health
```

If backend is not reachable from frontend, both containers may not be on `evalify_evalify-net`:

```bash
docker network inspect evalify_evalify-net
# Both evalify-backend and evalify-frontend should appear in "Containers"
```

### Port Already in Use

```bash
# Find what's using port 47823 (backend)
lsof -i :47823

# Find what's using port 5173 (frontend / Vite dev server)
lsof -i :5173

# Stop the local process before starting Docker
kill <PID>
```

**Common cause:** A local `uvicorn` or `npm run dev` process from non-Docker development is still running on the same port.

### MLflow not accessible at http://localhost:5005

```bash
docker logs evalify-mlflow | grep "Listening at"
# Should show: Listening at: http://0.0.0.0:5000
```

If it shows `127.0.0.1:5000`, the container is using an old image. Recreate it:

```bash
docker compose -f docker-compose.dev.yml rm -f mlflow
docker compose -f docker-compose.dev.yml up -d mlflow
```

### Ollama Not Reachable from Backend

```bash
docker exec evalify-backend curl http://host.docker.internal:11434/api/tags
```

If this fails:
1. Is Ollama running? `curl http://localhost:11434/api/tags`
2. Start Ollama: `ollama serve`
3. Check host-gateway is configured: `docker inspect evalify-backend | grep -A2 ExtraHosts`

Backend falls back to STUB mode automatically:
```
⚠️ Ollama: did not start — handwritten OCR will run in STUB mode
```

### Backend Image Build Fails (disk space / OOM)

The backend image is ~4–6 GB. Free up space:

```bash
docker system prune -f          # remove dangling images and stopped containers
docker image prune -a -f        # remove ALL unused images (careful!)
```

---

## What Was NOT Containerised

| Component | Reason |
|---|---|
| **Ollama** | Needs direct GPU/CUDA access. Running Ollama inside Docker requires `nvidia-container-toolkit` AND adds complexity. Running it on the host is simpler and already works reliably with GPUs attached. |

---

## Production Deployment Notes

Before deploying to production:

- [ ] Change JWT secrets in `teacher_credentials.env` and `student_credentials.env`
- [ ] Change MongoDB credentials from `evalify_dev_pass` to something strong
- [ ] Update `CORS_ORIGINS` to your actual domain (remove `http://localhost:*`)
- [ ] Enable HTTPS on the frontend (configure nginx SSL or use a reverse proxy like Traefik)
- [ ] Set up MongoDB backups (the `mongo-data` volume)
- [ ] Configure an S3-compatible artifact store for MLflow (replace SQLite)
- [ ] Limit container memory/CPU in docker-compose (`mem_limit`, `cpus`)
- [ ] Consider `nvidia-container-toolkit` to containerise Ollama as well
