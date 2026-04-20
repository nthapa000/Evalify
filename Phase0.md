# Phase 0 — Project Setup & Infrastructure

## Goal

Establish the monorepo skeleton, local development infrastructure (MongoDB + MLflow via Docker Compose), credential files, and placeholder code so that every subsequent phase has a clean, working foundation to build on.

---

## What Was Done in Phase 0

| Task | Output |
|------|--------|
| Monorepo scaffold | `frontend/`, `backend/`, `ml/`, `k8s/` directories |
| Version control | `.gitignore`, `.dvcignore` |
| Credentials | `teacher_credentials.env`, `student_credentials.env` |
| Dev infrastructure | `docker-compose.dev.yml` (MongoDB + MLflow) |
| DB seed | `backend/db/mongo-init.js` |
| Backend skeleton | `backend/app/main.py`, `requirements.txt`, `Dockerfile` |
| Frontend skeleton | React + Vite + Tailwind scaffold, `App.jsx`, `api.js`, `authStore.js` |
| ML stubs | `omr_service/app.py`, `trocr_service/app.py`, `llm_service/app.py` (all mock) |
| K8s stub | `k8s/namespace.yaml` |

---

## Overall System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BROWSER (React SPA)                         │
│  Teacher Pages          Student Pages                               │
│  - Create Paper         - Dashboard (subjects)                      │
│  - View Results         - Upload Answer Sheet                       │
│                         - View Result                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  HTTP REST  (Axios → /api/*)
                                │  JWT Bearer token on every request
┌───────────────────────────────▼─────────────────────────────────────┐
│                    BACKEND  (FastAPI  :8000)                         │
│                                                                     │
│  /auth   ──► JWT login for teacher & student                        │
│  /papers ──► CRUD for exam papers + answer keys + rubrics           │
│  /submit ──► accept uploaded answer sheet image                     │
│  /eval   ──► orchestrate ML pipeline, store result                  │
│  /result ──► return scores to teacher / student                     │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐  │
│  │ omr_client  │  │ trocr_client │  │      llm_client            │  │
│  │ calls :8001 │  │ calls :8002  │  │      calls :8003           │  │
│  └──────┬──────┘  └──────┬───────┘  └────────────┬───────────────┘  │
│         │                │                        │                  │
│  ┌──────▼────────────────▼────────────────────────▼───────────────┐  │
│  │                     MongoDB  :27017                            │  │
│  │   collections: users | papers | submissions | results         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               MLflow Tracking Server  :5000                  │   │
│  │  logs: OCR confidence | LLM latency | scores | model ver.   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                        │
┌────────▼──────┐   ┌─────────▼──────┐   ┌────────────▼────────────┐
│  OMR Service  │   │  TrOCR Service │   │    LLM Service          │
│  :8001        │   │  :8002         │   │    :8003 (Mistral 7B)   │
│  OpenCV       │   │  microsoft/    │   │    vLLM on V100 GPU     │
│  bubble detect│   │  trocr-base-   │   │                         │
│               │   │  handwritten   │   │                         │
└───────────────┘   └────────────────┘   └─────────────────────────┘
```

---

## Phase 0 — Infrastructure Flow

```
developer runs:
  docker compose -f docker-compose.dev.yml up -d
              │
              ├─► evalify-mongo  (port 27017)
              │       └─► runs mongo-init.js on first boot
              │           creates: evalify_db
              │           collections: users, papers, submissions, results
              │           indexes: email, roll_no, paper_id, submission_id
              │           seed rows: 1 teacher, 1 student
              │
              └─► evalify-mlflow  (port 5000)
                      └─► mlflow server --backend sqlite
                          artifact store: /mlflow/artifacts
                          UI: http://localhost:5000
```

---

## Directory Structure (after Phase 0)

```
Evalify/
│
├── frontend/                        React 18 + Vite + Tailwind SPA
│   ├── src/
│   │   ├── App.jsx                  Root router (placeholder in Phase 0)
│   │   ├── main.jsx                 ReactDOM bootstrap + providers
│   │   ├── index.css                Tailwind base imports
│   │   ├── pages/
│   │   │   ├── auth/                TeacherLogin, StudentLogin (Phase 1)
│   │   │   ├── teacher/             Dashboard, CreatePaper, PaperResults (Phase 1)
│   │   │   └── student/             Dashboard, SubjectPage, Submission, Result (Phase 1)
│   │   ├── components/
│   │   │   ├── ui/                  Button, Card, Modal, Badge (Phase 1)
│   │   │   ├── forms/               UploadZone, RubricBuilder, StepWizard (Phase 1)
│   │   │   └── layout/              Navbar, Sidebar, PageWrapper (Phase 1)
│   │   ├── hooks/                   useAuth, usePapers, useSubmission (Phase 2)
│   │   ├── services/
│   │   │   └── api.js               Single Axios instance with auth interceptor
│   │   ├── store/
│   │   │   └── authStore.js         Zustand: JWT in memory (never localStorage)
│   │   └── utils/                   validators.js, formatters.js (Phase 1)
│   ├── index.html                   SPA shell
│   ├── vite.config.js               Dev proxy /api → localhost:8000
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── Dockerfile                   Multi-stage: Node build → Nginx static
│   └── nginx.conf                   SPA fallback + asset caching
│
├── backend/                         FastAPI Python 3.11 API
│   ├── app/
│   │   ├── main.py                  FastAPI app + CORS + /health endpoint
│   │   ├── routers/                 auth.py, papers.py, submissions.py, results.py (Phase 2)
│   │   ├── models/                  Pydantic schemas per domain (Phase 2)
│   │   ├── services/                omr_client.py, trocr_client.py, llm_client.py (Phase 3+)
│   │   └── db/
│   │       ├── mongodb.py           Motor async connection (Phase 2)
│   │       └── mlflow_logger.py     MLflow logging helpers (Phase 5)
│   ├── db/
│   │   └── mongo-init.js            MongoDB seed script (runs on first container boot)
│   ├── tests/                       Pytest test suite (Phase 2)
│   ├── requirements.txt             Python dependencies (FastAPI, Motor, JWT, MLflow …)
│   └── Dockerfile                   python:3.11-slim image
│
├── ml/                              ML microservices (each is a separate FastAPI app)
│   ├── omr_service/
│   │   └── app.py                   Phase 0: mock | Phase 3: OpenCV OMR detection
│   ├── trocr_service/
│   │   └── app.py                   Phase 0: mock | Phase 3: TrOCR inference
│   └── llm_service/
│       └── app.py                   Phase 0: mock | Phase 5: Mistral 7B via vLLM
│
├── k8s/                             Kubernetes manifests (Phase 7)
│   ├── namespace.yaml               evalify namespace
│   ├── configmaps/                  env vars per service
│   ├── secrets/                     base64-encoded credentials
│   ├── deployments/                 one Deployment per service
│   ├── services/                    ClusterIP (internal) + NodePort (external)
│   └── pvc.yaml                     Persistent volumes for MongoDB + MLflow
│
├── mlflow/                          MLflow compose override (Phase 0 uses docker-compose.dev.yml)
│
├── docker-compose.dev.yml           Local dev: MongoDB + MLflow only
├── .gitignore
├── .dvcignore
├── teacher_credentials.env          JWT secret + default teacher login
├── student_credentials.env          JWT secret + seed student
└── EVALIFY_PLAN.md                  Master project plan
```

---

## File-by-File Purpose

### `docker-compose.dev.yml`
Spins up two containers for local development:
- **evalify-mongo** — MongoDB 7 with the `evalify_db` database. Runs `mongo-init.js` on first boot to create collections, indexes, and seed users. Exposes port `27017` to the host so the FastAPI backend (running outside Docker in dev) can connect with `mongodb://evalify:evalify_dev_pass@localhost:27017/evalify_db`.
- **evalify-mlflow** — MLflow 2.13 tracking server backed by SQLite. Artifacts (grading JSONs, answer sheet images) stored in a named volume. UI reachable at `http://localhost:5000`.

### `backend/db/mongo-init.js`
JavaScript init script mounted into the MongoDB container. MongoDB executes it once when the data directory is empty (i.e., first run). Creates all four collections, adds unique indexes for fast teacher/student lookup, and inserts one seed teacher and one seed student with placeholder bcrypt hashes.

### `backend/app/main.py`
Bare-bones FastAPI app. Sets up CORS so the Vite dev server on port `5173` can make API calls. Registers a `/health` endpoint used by Kubernetes liveness probes. Actual routers (`/auth`, `/papers`, etc.) are added in Phase 2.

### `backend/requirements.txt`
Pinned Python dependencies. Key packages:
- `fastapi` + `uvicorn` — web framework and ASGI server
- `motor` — async MongoDB driver (works with FastAPI's async event loop)
- `PyJWT` + `bcrypt` — JWT signing and password hashing
- `pydantic-settings` — loads `.env` files into typed Settings objects
- `mlflow` — experiment tracking client library

### `frontend/src/services/api.js`
Singleton Axios instance. All API calls in the app go through this one object. The request interceptor attaches the JWT Bearer token. This means no page or hook ever hardcodes auth headers — they just use `api.get(...)` and auth is automatic.

### `frontend/src/store/authStore.js`
Zustand store holding `token` and `user` in JavaScript memory. Deliberately not persisted to `localStorage` to prevent XSS token theft. On page refresh the user is logged out (acceptable trade-off for academic tool). Phase 2 adds `setAuth` / `clearAuth` calls from the login pages.

### `teacher_credentials.env` / `student_credentials.env`
Environment variable files loaded by FastAPI at startup via `pydantic-settings`. Contain JWT secrets and seed credentials. **Not committed to git** (listed in `.gitignore`). In production, inject as Kubernetes Secrets.

### `ml/*/app.py` (three stub services)
Each is a standalone FastAPI microservice that will run on its own port:
- `omr_service` `:8001` — receives an image, returns `{Q1: "A", Q2: "B", ...}`
- `trocr_service` `:8002` — receives an image, returns extracted text + per-section split
- `llm_service` `:8003` — receives question + rubric + student answer, returns JSON grading result

All three return mock data with a 2-second sleep in Phase 0. The backend's `services/omr_client.py` etc. will call these via HTTP (not import them) so they scale independently.

---

## How to Start the Dev Environment

```bash
# 1. Start MongoDB and MLflow
docker compose -f docker-compose.dev.yml up -d

# 2. Verify containers are healthy
docker compose -f docker-compose.dev.yml ps

# 3. Check MLflow UI
open http://localhost:5000

# 4. (Phase 2 onwards) Start FastAPI backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 5. (Phase 1 onwards) Start React frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Phase Checklist

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Infrastructure setup (this document) | Done |
| Phase 1 | Frontend shell with mock data | Pending |
| Phase 2 | Backend API + MongoDB + JWT auth | Pending |
| Phase 3 | Type 1 MCQ evaluation (OMR + TrOCR) | Pending |
| Phase 4 | Type 2 MCQ + Numerical (tolerance grading) | Pending |
| Phase 5 | Type 3 Subjective + LLM + MLflow | Pending |
| Phase 6 | Docker containerisation | Pending |
| Phase 7 | Kubernetes deployment with GPU scheduling | Pending |
| Phase 8 | Production deploy (HF Spaces + V100) | Pending |
