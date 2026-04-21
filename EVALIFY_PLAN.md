# Evalify — Automated Handwritten Answer Sheet Evaluation System
### Project Plan & Implementation Roadmap
**Team:** m25csa019 (Nishant Thapa), m25csa021 (Pranav)
**Subject:** MLOps / DLOps
**Date:** April 2026

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture Design](#2-architecture-design)
3. [Technology Stack Justification](#3-technology-stack-justification)
4. [Paper Types & Evaluation Pipeline](#4-paper-types--evaluation-pipeline)
5. [Prompt Engineering & Grading Rubric](#5-prompt-engineering--grading-rubric)
6. [MLOps: Experiment Tracking & Model Versioning](#6-mlops-experiment-tracking--model-versioning)
7. [Step-by-Step Implementation Plan](#7-step-by-step-implementation-plan)
8. [Docker Strategy](#8-docker-strategy)
9. [Deployment Strategy](#9-deployment-strategy)
10. [Directory Structure](#10-directory-structure)
11. [API Contract](#11-api-contract)

---

## 1. Project Overview

**Evalify** is a web-based platform that automates evaluation of handwritten answer sheets. Teachers create exam papers of three types; students upload scanned answer sheets; the system evaluates and returns scores using CV, OCR, and LLM models.

### Roles
| Role | Capabilities |
|------|-------------|
| Teacher | Create papers, upload answer keys, set rubrics, view all results |
| Student | Login, view available exams, upload answer sheet, view results |

### Paper Types
| Type | Short Name | Evaluation Method |
|------|-----------|-------------------|
| MCQ only | Type 1 | OMR (OpenCV heuristic) or Ollama vision model |
| MCQ + Numerical | Type 2 | Ollama vision + tolerance-based numerical grading |
| MCQ + Numerical + Subjective | Type 3 | Ollama vision + LLM rubric grading (same model) |

---

## 2. Architecture Design

```
┌─────────────────────────────────────────────────────────┐
│                        CLIENT                           │
│              React (Vite) SPA                           │
│         Teacher View  |  Student View                   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST / JSON
┌──────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│  /auth  /papers  /submissions  /results                 │
│                                                         │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │   OMR Service   │  │   Ollama Vision Service       │  │
│  │   (OpenCV)      │  │   llama3.2-vision:11b         │  │
│  │   heuristic     │  │   MCQ extract + LLM grading   │  │
│  │   bubble detect │  │   (runs on V100 via Ollama)   │  │
│  └─────────────────┘  └──────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           MongoDB  (paper/result store)           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           MLflow  (experiment tracking)           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                       │
          ┌────────────▼─────────────┐
          │    Docker Compose        │
          │  (single V100 server)    │
          │  frontend · backend      │
          │  mongodb · mlflow        │
          │  ollama                  │
          └──────────────────────────┘
```

### Why a single Docker Compose (no Kubernetes)?
- The project runs on a single shared V100 server — Kubernetes adds orchestration overhead with no benefit at this scale
- Docker Compose provides service isolation, volume mounts, and a shared network with far less configuration
- Kubernetes can be adopted later if the system needs to scale across multiple nodes

---

## 3. Technology Stack Justification

### Frontend
| Tech | Reason |
|------|--------|
| React + Vite | Fast HMR, lightweight build output |
| TailwindCSS | Utility-first, no runtime overhead, consistent design tokens |
| React Router v6 | Nested layouts with route guards |
| Axios | Clean interceptor pattern for auth tokens |

### Backend
| Tech | Reason |
|------|--------|
| FastAPI (Python) | Async, automatic OpenAPI docs, natively supports numpy/PIL |
| Uvicorn | Production-grade ASGI serving |
| Pydantic v2 | Request/response validation and serialization |
| pdfplumber | Reliable PDF text extraction for typed answer key PDFs |

### Database — MongoDB
- Answer sheets, rubrics, and results are document-shaped (no fixed schema across paper types)
- Each paper type has different metadata fields; a relational schema would need NULL-heavy tables or complex joins
- Motor (async) integrates cleanly with FastAPI

### ML / AI Models

| Task | Model | Why |
|------|-------|-----|
| OMR bubble detection | OpenCV heuristic (contour detection) | Zero-weight, deterministic, works on any OMR layout without a template. Uses a hybrid fill-ratio strategy: strict threshold for clear marks, dominance-based fallback for light pencil fills. |
| Handwritten MCQ extraction | `llama3.2-vision:11b` via Ollama | TrOCR (microsoft/trocr-base-handwritten) was trialled first but hallucinated full English sentences because it was trained on the IAM sentence dataset, not isolated MCQ letters. EasyOCR was trialled next but gave avg confidence of 0.36 on single handwritten characters. Ollama with a vision-language model reliably returns structured JSON from the MCQ prompt. |
| Subjective LLM evaluation | `llama3.2-vision:11b` via Ollama | Same model as OCR — avoids running two separate models on the GPU. 11B parameters fit comfortably on the V100 (32GB VRAM). Instruction-following is strong enough for rubric-based grading. |

#### Why Ollama (not vLLM or llama.cpp)?
- User-space install — no sudo required on shared DGX server
- Single binary manages model download, serving, and GPU allocation
- `/api/generate` endpoint is simple HTTP; no OpenAI SDK dependency
- GPU acceleration confirmed working at ~14s per inference on V100 (vs 92s on CPU)

#### Ollama GPU setup note
On the DGX server, GPU libraries must be copied from the tarball:
```bash
cp -r /tmp/lib/ollama/* ~/.local/lib/ollama/
export LD_LIBRARY_PATH=/usr/lib64:$LD_LIBRARY_PATH
```
See `backend/Ollama.md` for full setup instructions.

### MLOps
| Tool | Purpose |
|------|---------|
| MLflow | Log OCR confidence scores, LLM grading scores, model versions per run |
| Model Registry (MLflow) | Tag model versions as Staging / Production |

---

## 4. Paper Types & Evaluation Pipeline

### Type 1 — MCQ Only

#### Sub-type 1a: OMR Sheet
```
Upload image → Preprocess (grayscale, Gaussian blur, adaptive threshold)
→ Detect circular contours (OpenCV findContours + circularity filter)
→ Cluster contours into rows (Y-coordinate tolerance = 45px,
   handles scan tilt on 2-column sheets)
→ For each question row: detect ALL filled bubbles using hybrid strategy:
     Primary:  filled_px / contour_area >= 0.28
     Fallback: ratio >= 0.16 AND ratio >= per-question mean × 1.8
→ Multi-answer support: "A,C" if student fills both A and C
→ Compare with answer key (frozenset exact-match — no partial credit,
   overfill earns zero)
→ Score = Σ (correct × marks_per_question)
```

**Key design decisions:**
- No template required — the heuristic works on any OMR layout
- Multi-column sheets (e.g. Q1–Q10 left, Q11–Q20 right) handled by detecting large X-gaps between bubble groups in a row
- ROW_TOLERANCE = 45px prevents paired rows being split when left/right columns have scan-tilt offset

#### Sub-type 1b: Handwritten MCQ Sheet
```
Upload image → Ollama vision (llama3.2-vision:11b)
→ Prompt: "The paper has exactly N questions Q1–QN.
   Return ONLY a JSON object {Q1: 'A', Q2: 'B,C', ...}
   If a question is blank, omit it."
→ Parse JSON response (json.loads, regex fallback)
→ Compare with answer key
→ Score
```

**Why not TrOCR or EasyOCR:**
- `microsoft/trocr-base-handwritten` is fine-tuned on the IAM dataset (full handwritten sentences). When given an MCQ answer sheet it hallucinates complete English sentences instead of single letters.
- EasyOCR performs character-level detection. Average confidence on isolated single handwritten letters was 0.36 — too unreliable for grading.
- Ollama vision model understands the task context from the prompt and returns structured JSON directly.

### Type 2 — MCQ + Numerical
```
Upload image → Ollama vision inference
→ Separate MCQ section answers from Numerical section answers
→ MCQ: exact match grading
→ Numerical: tolerance-based grading (see below)
→ Score
```

**Numerical Tolerance Handling:**
```json
{
  "question_id": "N1",
  "correct_answer": 3.5,
  "tolerance_type": "range",
  "tolerance_value": 0.1,
  "accepted_variants": ["3.5", "3.50", "7/2"]
}
```
- `exact`: string match after normalization
- `range`: `abs(student - correct) <= tolerance_value`
- `decimal_variants`: check against explicit accepted_variants list

### Type 3 — MCQ + Numerical + Subjective
```
Upload image → Ollama vision inference
→ MCQ section → exact match
→ Numerical section → tolerance grading
→ Subjective section text extracted via Ollama vision
→ Ollama LLM grades subjective using structured rubric (same model, text-only prompt)
→ Combined score logged to MLflow
```

---

## 5. Prompt Engineering & Grading Rubric

### MCQ Extraction Prompt (`backend/app/prompts/prompt_mcq.py`)

```python
def build_mcq_prompt(mcq_count: int, options: str = "A, B, C, D") -> str:
    return f"""You are reading a student's handwritten MCQ answer sheet.

The paper has exactly {mcq_count} questions numbered 1 to {mcq_count}.
Valid options are: {options}.

IMPORTANT — a student may circle or write MORE THAN ONE option for a question.
- If only one option is written (e.g. "B"), the value is just "B".
- If multiple options are written (e.g. both "A" and "C"), join them with a
  comma in alphabetical order: "A,C".
- If a question is blank or completely unreadable, skip it entirely.

Return ONLY a JSON object — no explanation, no preamble, no trailing text.
Keys: "Q1" to "Q{mcq_count}". Values: sorted comma-joined option letters."""
```

### Subjective Grading Prompt (LLM)

```python
GRADING_SYSTEM_PROMPT = """
You are an expert academic evaluator. Grade strictly based on the rubric.
Rules:
- Award marks ONLY for concepts explicitly present in the student's answer.
- Do NOT penalize for writing style unless language_quality is specified.
- Partial credit is allowed if partial_credit is true.
- Response MUST be valid JSON — no extra text.
- If the student answer is blank or illegible, award 0.
"""

GRADING_USER_PROMPT = """
Question: {question_text}
Maximum Marks: {max_marks}
Rubric:
- Key Concepts: {key_concepts}
- Mandatory Concepts: {mandatory_concepts}
- Marks per concept: {marks_per_concept}
- Partial credit: {partial_credit}
Model Answer (reference only): {model_answer}
Student's Answer: {student_answer}

Return JSON:
{{
  "concepts_found": [...],
  "concepts_missing": [...],
  "mandatory_met": true/false,
  "raw_score": <float>,
  "capped_score": <float 0–{max_marks}>,
  "feedback": "<one sentence>"
}}
"""
```

**Why temperature = 0.1?** Grading must be deterministic — the same answer must always receive the same score.

---

## 6. MLOps: Experiment Tracking & Model Versioning

### MLflow Setup
```
mlflow/
├── tracking server  (port 5000, runs as Docker service)
└── artifact store   (local volume mounted at ./mlflow-data)
```

**What is logged per evaluation run:**
```python
with mlflow.start_run(run_name=f"eval_{submission_id}"):
    mlflow.log_metric("ocr_confidence_avg", avg_confidence)
    mlflow.log_metric("total_score", final_score)
    mlflow.log_metric("max_possible_score", max_score)
    mlflow.log_metric("llm_grading_latency_s", latency)   # Type 3 only
    mlflow.log_param("ollama_model", OLLAMA_MODEL)
    mlflow.log_param("paper_type", paper_type)
    mlflow.log_dict(grading_result, "grading_result.json")
```

### Model Registry
```
Model Registry:
└── Ollama-Vision-Grader
    ├── Version 1: llama3.2-vision:11b  [Production]
    └── Version 2: (future fine-tune)   [Staging]
```

---

## 7. Step-by-Step Implementation Plan

### Phase 0 — Project Setup ✅
- [x] Create monorepo: `frontend/`, `backend/`
- [x] Initialize git + `.gitignore`
- [x] Set up MongoDB (Docker single container via `docker-compose.dev.yml`)
- [x] Set up MLflow tracking server (Docker single container)
- [x] Write base `docker-compose.dev.yml` for local development

---

### Phase 1 — Frontend Shell ✅
- [x] Scaffold React + Vite + TailwindCSS
- [x] React Router v6 with route guards
- [x] Layout components: `Navbar`, `Sidebar`, `Card`, `Button`, `Modal`
- [x] Auth pages: `TeacherLogin`, `StudentLogin`
- [x] Teacher pages: `TeacherDashboard`, `CreatePaper` (5-step wizard), `PaperResults`
- [x] Student pages: `StudentDashboard`, `SubmissionPage`, `ResultPage`
- [x] Loading skeletons, success modals, toasts
- [x] Full UI flow works with mock data

---

### Phase 2 — Backend Foundation ✅
- [x] FastAPI app with routers: `/auth`, `/papers`, `/submissions`, `/results`
- [x] MongoDB with Motor (async)
- [x] JWT auth (HS256)
- [x] `/auth/teacher/login` and `/auth/student/login`
- [x] CRUD for papers: `POST /papers`, `GET /papers`, `GET /papers/{id}`, `DELETE /papers/{id}`
- [x] `POST /submissions` — store file + metadata
- [x] `GET /results/{submission_id}` and `GET /results/paper/{paper_id}`
- [x] CORS middleware for React dev server
- [x] Frontend ↔ Backend communication verified

---

### Phase 3 — Type 1 MCQ Evaluation ✅
- [x] OMR engine (`backend/app/services/omr_engine.py`):
  - Adaptive threshold + contour-based bubble detection
  - Row clustering with `ROW_TOLERANCE = 45px` (handles scan tilt on 2-column sheets)
  - Multi-column layout detection via large X-gap splitting
  - Hybrid fill detection: primary absolute threshold (0.28) + dominance fallback (0.16, ×1.8)
  - Multi-answer support: returns "A,C" when both A and C are filled
  - **No template required** — generalised heuristic works on any OMR layout
- [x] Tried `microsoft/trocr-base-handwritten` → **rejected**: hallucinated English sentences (IAM dataset bias)
- [x] Tried EasyOCR → **rejected**: avg confidence 0.36 on single handwritten characters
- [x] Ollama vision engine (`backend/app/services/trocr_engine.py` — now Ollama-backed):
  - Sends base64 image + MCQ prompt to `llama3.2-vision:11b` via `/api/generate`
  - Parses JSON response with `json.loads`, falls back to regex
  - GPU-accelerated on V100 via Ollama (~14s/request)
- [x] MCQ grading with `frozenset` exact-match, multi-answer aware
- [x] Negative marking support (all questions or per-question scope)
- [x] Answer key PDF extraction via `pdfplumber`
- [x] MLflow logging per evaluation run
- [x] Real MCQ OMR → correct score returned

---

### Phase 4 — Type 2 MCQ + Numerical (In Progress)
- [ ] Extend Ollama prompt to segment MCQ vs Numerical sections
- [ ] Implement numerical tolerance grader
- [ ] Extend teacher paper-creation UI: add per-numerical-question tolerance fields
- [ ] Extend `/evaluate` to handle Type 2 logic
- [ ] Test: Upload Type 2 sheet → MCQ + numerical both graded correctly

---

### Phase 5 — Type 3 MCQ + Numerical + Subjective (Planned)
- [ ] Extend Ollama vision prompt for subjective text extraction
- [ ] Implement LLM grading service with rubric prompt (Section 5)
- [ ] Extend teacher UI: rubric input per subjective question
- [ ] Wire full Type 3 pipeline in evaluator
- [ ] Add MLflow logging for LLM latency + scores
- [ ] Test: Full Type 3 submission → correct composite score

---

### Phase 6 — Docker Containerisation & Deployment (Planned)
- [ ] Write `Dockerfile` for each service:
  - `frontend` — Node build → Nginx static serve (~25MB)
  - `backend` — Python 3.11 slim + FastAPI (~400MB)
  - `mongodb` — official `mongo:7` image
  - `mlflow` — official `mlflow` image
  - `ollama` — official `ollama/ollama` image with GPU passthrough
- [ ] Write `docker-compose.prod.yml` with all services wired together
- [ ] Configure Ollama GPU access inside Docker (`--gpus all` or `deploy.resources.reservations`)
- [ ] Test: `docker-compose -f docker-compose.prod.yml up` — all services healthy, end-to-end flow works
- [ ] Final end-to-end test on production URLs

---

## 8. Docker Strategy

### Service Map
| Service | Image | Port | Notes |
|---------|-------|------|-------|
| frontend | custom (Node → Nginx) | 80 | Static React build served by Nginx |
| backend | custom (Python 3.11 slim) | 8000 | FastAPI + Uvicorn |
| mongodb | mongo:7 | 27017 | Persistent volume for data |
| mlflow | ghcr.io/mlflow/mlflow | 5000 | Persistent volume for artifacts |
| ollama | ollama/ollama | 11434 | GPU passthrough required |

### Dockerfiles

```dockerfile
# frontend — multi-stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Final image: ~25MB
```

```dockerfile
# backend — slim Python
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.prod.yml (outline)
```yaml
services:
  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - MONGO_URL=mongodb://mongodb:27017/evalify_db
      - OLLAMA_HOST=http://ollama:11434
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on: [mongodb, ollama, mlflow]
    volumes:
      - ./backend/uploads:/app/uploads

  mongodb:
    image: mongo:7
    volumes:
      - mongo_data:/data/db

  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    ports: ["5000:5000"]
    volumes:
      - mlflow_data:/mlflow
    command: mlflow server --host 0.0.0.0 --port 5000 --default-artifact-root /mlflow/artifacts

  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  mongo_data:
  mlflow_data:
  ollama_data:
```

---

## 9. Deployment Strategy

```
V100 Server (on-premise)
└── Docker Compose
    ├── frontend    (port 80)   ← students and teachers access this
    ├── backend     (port 8000) ← API, internal only behind Nginx
    ├── mongodb     (port 27017, internal only)
    ├── mlflow      (port 5000, admin access)
    └── ollama      (port 11434, internal only)
```

**Access pattern:**
- All traffic enters through the frontend Nginx container
- `/api/*` requests are reverse-proxied to the backend container
- Ollama, MongoDB, and MLflow are internal Docker network services (not exposed to the internet)

---

## 10. Directory Structure

```
evalify/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── auth/          TeacherLogin.jsx, StudentLogin.jsx
│   │   │   ├── teacher/       Dashboard.jsx, CreatePaper.jsx, PaperResults.jsx
│   │   │   └── student/       Dashboard.jsx, SubmissionPage.jsx, ResultPage.jsx
│   │   ├── components/
│   │   │   ├── ui/            Button.jsx, Card.jsx, Modal.jsx, Badge.jsx
│   │   │   ├── forms/         UploadZone.jsx, RubricBuilder.jsx, StepWizard.jsx
│   │   │   └── layout/        Navbar.jsx, Sidebar.jsx, PageWrapper.jsx
│   │   ├── hooks/             useAuth.js, usePapers.js, useSubmission.js
│   │   ├── services/          api.js (axios instance + interceptors)
│   │   ├── store/             authStore.js (Zustand)
│   │   └── utils/             validators.js, formatters.js
│   ├── Dockerfile
│   └── nginx.conf
│
├── backend/
│   ├── app/
│   │   ├── routers/           auth.py, papers.py, submissions.py, results.py
│   │   ├── models/            paper.py, submission.py, user.py
│   │   ├── services/
│   │   │   ├── omr_engine.py       # OpenCV heuristic bubble detector
│   │   │   ├── trocr_engine.py     # Ollama vision MCQ extractor (name kept for compatibility)
│   │   │   ├── evaluator.py        # Routes to correct engine, grades, logs to MLflow
│   │   │   └── pdf_extractor.py    # pdfplumber answer key extraction
│   │   ├── prompts/
│   │   │   └── prompt_mcq.py       # MCQ extraction prompt template
│   │   ├── db/                mongodb.py, seed.py, mlflow_logger.py
│   │   └── main.py
│   ├── uploads/               student submission images (volume-mounted)
│   ├── venv/                  Python virtual environment (not in Docker image)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── start.sh               dev startup: launches Ollama, activates venv, starts uvicorn
│   └── Ollama.md              Ollama user-space install guide for shared DGX server
│
├── docker-compose.dev.yml     MongoDB + MLflow only (Ollama + backend run natively in dev)
├── docker-compose.prod.yml    All services including frontend, backend, ollama
├── teacher_credentials.env
├── student_credentials.env
└── EVALIFY_PLAN.md
```

---

## 11. API Contract

### Auth
```
POST /api/auth/teacher/login    { email, password }   → { token, teacher_id }
POST /api/auth/student/login    { roll_no, password } → { token, student_id }
```

### Papers (Teacher)
```
POST   /api/papers                  Create paper
GET    /api/papers                  List teacher's papers
GET    /api/papers/available        Papers available to student
POST   /api/papers/files/upload     Upload PDF or image, return server URL
GET    /api/papers/files/{filename} Serve uploaded file
POST   /api/papers/extract-answers  Extract MCQ answers from answer key PDF
GET    /api/papers/{id}             Get paper detail
DELETE /api/papers/{id}             Delete paper
```

### Submissions (Student)
```
POST   /api/submissions                  Upload answer sheet
GET    /api/submissions/{id}/status      Evaluation status (pending/evaluated/error)
```

### Results
```
GET    /api/results/{submission_id}       Individual result
GET    /api/results/paper/{paper_id}      All results for a paper (teacher view)
```

---

## Green Signal Checklist

| Signal | Condition | Phase | Status |
|--------|-----------|-------|--------|
| #1 | All UI pages render, navigation works, mock data displays | Phase 1 | ✅ Done |
| #2 | Frontend ↔ Backend API works, auth flow complete, papers saved to MongoDB | Phase 2 | ✅ Done |
| #3 | Type 1 MCQ OMR sheet uploaded → real score returned | Phase 3 | ✅ Done |
| #4 | Type 1 handwritten MCQ sheet → Ollama extracts answers, score returned | Phase 3 | ✅ Done |
| #5 | Type 2 sheet → MCQ + numerical both graded with tolerance | Phase 4 | ⬜ Pending |
| #6 | Type 3 sheet → LLM grades subjective, MLflow logs run | Phase 5 | ⬜ Pending |
| #7 | `docker-compose -f docker-compose.prod.yml up` — all services healthy | Phase 6 | ⬜ Pending |
| #8 | Live URL accessible, end-to-end flow on production server | Phase 6 | ⬜ Pending |

---

*Last updated: April 21, 2026*
