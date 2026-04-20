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
8. [Docker & Kubernetes Strategy](#8-docker--kubernetes-strategy)
9. [Deployment Strategy](#9-deployment-strategy)
10. [Directory Structure](#10-directory-structure)
11. [API Contract](#11-api-contract)
12. [Updated Prompt for Code Generation](#12-updated-prompt-for-code-generation)

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
| MCQ only | Type 1 | OMR (OpenCV) or TrOCR |
| MCQ + Numerical | Type 2 | TrOCR + tolerance-based numerical grading |
| MCQ + Numerical + Subjective | Type 3 | TrOCR + LLM (Mistral 7B on V100 server) |

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
│  /auth  /papers  /submit  /evaluate  /results           │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ OMR      │  │ TrOCR    │  │  LLM Inference       │  │
│  │ Service  │  │ Service  │  │  Service (Mistral 7B) │  │
│  │(OpenCV)  │  │(HF model)│  │  (runs on V100)      │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
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
┌──────────────────────▼──────────────────────────────────┐
│              Kubernetes Cluster                         │
│  Deployments: frontend, backend, omr, trocr, llm,      │
│              mongodb, mlflow                            │
│  Services + Ingress + PVC                               │
└─────────────────────────────────────────────────────────┘
```

### Why Separate Backend and Frontend?
- Independent scaling (LLM inference is heavy; frontend is static)
- Frontend can be deployed to Hugging Face Spaces (free, static hosting)
- Backend + model services run on your V100 server
- Clean API boundary makes swapping models easy

---

## 3. Technology Stack Justification

### Frontend
| Tech | Reason |
|------|--------|
| React + Vite | Fast HMR, lightweight build output, easy HF Spaces deploy |
| TailwindCSS | Utility-first, no runtime overhead, consistent design tokens |
| React Router v6 | File-based routing mental model, nested layouts |
| Axios | Clean interceptor pattern for auth tokens |
| React Query | Caching + loading states out of the box |

### Backend
| Tech | Reason |
|------|--------|
| FastAPI (Python) | Async, automatic OpenAPI docs, natively supports numpy/PIL |
| Uvicorn + Gunicorn | Production-grade ASGI serving |
| Python-multipart | File upload handling |
| Pydantic v2 | Request/response validation, serialization |

### Database — MongoDB
**Justification (addressing TA feedback):**
- Answer sheets, rubrics, and results are document-shaped (no fixed schema across paper types)
- Each paper type has different metadata fields; a relational schema would need NULL-heavy tables or complex joins
- GridFS (built into MongoDB) stores uploaded images alongside metadata — no separate file storage needed for v1
- PyMongo / Motor (async) integrates cleanly with FastAPI
- Easy to add indexes on `student_id`, `paper_id`, `subject` for query performance

### ML / AI Models
| Task | Model | Why |
|------|-------|-----|
| OMR bubble detection | OpenCV (findContours + HoughCircles) | Zero-weight, deterministic, fast; OMR is a geometry problem not a learning problem |
| Handwriting OCR | `microsoft/trocr-base-handwritten` (HuggingFace) | State-of-art on IAM dataset, ~350MB, runs on CPU or GPU |
| Subjective LLM evaluation | Mistral-7B-Instruct-v0.3 (GGUF via llama.cpp or vLLM) | 7B fits on one V100-32GB comfortably; fast inference; strong instruction following |
| (Alternative OCR) | `Salesforce/blip2-opt-2.7b` | If TrOCR accuracy is low on domain data |

### MLOps
| Tool | Purpose |
|------|---------|
| MLflow | Log OCR confidence scores, LLM grading scores, model versions per run |
| DVC | Version answer-key datasets and fine-tuned model weights |
| Model Registry (MLflow) | Tag model versions as Staging / Production |

---

## 4. Paper Types & Evaluation Pipeline

### Type 1 — MCQ Only

#### Sub-type 1a: OMR Sheet
```
Upload image → Preprocess (grayscale, threshold, deskew)
→ Detect bubble regions (OpenCV contour detection)
→ Check filled bubble per question
→ Compare with answer key
→ Score = Σ (correct × marks_per_question)
```
**OpenCV approach:** Divide the sheet into a grid of ROIs (regions of interest). For each question row, find the darkest filled circle using `cv2.countNonZero` after thresholding. This is robust and requires no ML.

#### Sub-type 1b: Normal Written MCQ
```
Upload image → TrOCR inference
→ Parse "1. A  2. B  3. C ..." pattern
→ Compare with answer key
→ Score
```

### Type 2 — MCQ + Numerical
```
Upload image → TrOCR inference
→ Separate MCQ section answers from Numerical section answers
→ MCQ: exact match grading
→ Numerical: tolerance-based grading (see below)
→ Score
```

**Numerical Tolerance Handling:**
When teacher creates paper, for each numerical question they specify:
```json
{
  "question_id": "N1",
  "correct_answer": 3.5,
  "tolerance_type": "range",        // "exact" | "range" | "decimal_variants"
  "tolerance_value": 0.1,           // ±0.1 means 3.4–3.6 accepted
  "accepted_variants": ["3.5", "3.50", "7/2"]  // optional explicit list
}
```
Grading logic:
- `exact`: string match after normalization (strip trailing zeros)
- `range`: `abs(student_answer - correct_answer) <= tolerance_value`
- `decimal_variants`: check against `accepted_variants` list

### Type 3 — MCQ + Numerical + Subjective
```
Upload image → TrOCR inference
→ MCQ section → exact match
→ Numerical section → tolerance grading
→ Subjective section text extracted
→ LLM grading (see Section 5)
→ Combined score
```

---

## 5. Prompt Engineering & Grading Rubric

### Rubric Structure (Teacher Input)
When creating a Type 3 paper, the teacher provides per-question rubrics:

```json
{
  "question_id": "S1",
  "question_text": "Explain the working of a transformer model.",
  "max_marks": 10,
  "rubric": {
    "key_concepts": [
      "self-attention mechanism",
      "positional encoding",
      "encoder-decoder structure",
      "multi-head attention"
    ],
    "mandatory_concepts": ["self-attention mechanism"],
    "partial_credit": true,
    "marks_per_concept": 2.5,
    "language_quality_weight": 0.1
  },
  "model_answer": "A transformer uses self-attention to..."
}
```

### LLM Prompt Template

```python
GRADING_SYSTEM_PROMPT = """
You are an expert academic evaluator. Your task is to grade a student's answer 
strictly based on the provided rubric. Be objective, consistent, and fair.

Rules:
- Award marks ONLY for concepts explicitly present in the student's answer.
- Do NOT penalize for writing style unless language_quality is specified.
- Partial credit is allowed if partial_credit is true in the rubric.
- Your response MUST be valid JSON — no extra text outside the JSON block.
- If the student answer is blank or illegible, award 0.
"""

GRADING_USER_PROMPT = """
Question: {question_text}

Maximum Marks: {max_marks}

Rubric:
- Key Concepts to check: {key_concepts}
- Mandatory Concepts (must be present for any marks): {mandatory_concepts}
- Marks per concept: {marks_per_concept}
- Partial credit allowed: {partial_credit}

Model Answer (for reference only):
{model_answer}

Student's Answer (extracted via OCR):
{student_answer}

Return your evaluation as JSON in this exact format:
{{
  "concepts_found": ["list", "of", "matched", "concepts"],
  "concepts_missing": ["list", "of", "missing", "concepts"],
  "mandatory_met": true/false,
  "raw_score": <float>,
  "capped_score": <float between 0 and {max_marks}>,
  "feedback": "<one sentence explaining the grade>"
}}
"""
```

### Grading Pipeline (Python pseudocode)
```python
def grade_subjective(question, student_answer_text):
    prompt = GRADING_USER_PROMPT.format(
        question_text=question["question_text"],
        max_marks=question["max_marks"],
        key_concepts=question["rubric"]["key_concepts"],
        mandatory_concepts=question["rubric"]["mandatory_concepts"],
        marks_per_concept=question["rubric"]["marks_per_concept"],
        partial_credit=question["rubric"]["partial_credit"],
        model_answer=question["model_answer"],
        student_answer=student_answer_text
    )
    
    response = llm_client.generate(
        system=GRADING_SYSTEM_PROMPT,
        user=prompt,
        temperature=0.1,      # Low temperature for consistency
        max_tokens=512,
        response_format="json"
    )
    
    result = json.loads(response)
    
    # Safety clamp
    result["capped_score"] = min(result["capped_score"], question["max_marks"])
    result["capped_score"] = max(result["capped_score"], 0)
    
    # Log to MLflow
    mlflow.log_metric(f"q{question['id']}_llm_score", result["capped_score"])
    
    return result
```

### Why Low Temperature (0.1)?
Grading must be **deterministic and consistent** — the same answer should always receive the same score. Higher temperature introduces randomness which is unacceptable in academic evaluation.

### Handling OCR Errors in LLM Prompt
Add OCR confidence score to the prompt:
```
Note: This text was extracted via OCR with {confidence}% confidence. 
Minor spelling errors may be OCR artifacts — focus on semantic meaning.
```

---

## 6. MLOps: Experiment Tracking & Model Versioning

### MLflow Setup

```
mlflow/
├── tracking server  (port 5000)
└── artifact store   (local volume or S3-compatible MinIO)
```

**What to track per evaluation run:**
```python
with mlflow.start_run(run_name=f"eval_{submission_id}"):
    # OCR metrics
    mlflow.log_metric("ocr_confidence_avg", avg_confidence)
    mlflow.log_metric("ocr_word_count", word_count)
    
    # LLM grading metrics  
    mlflow.log_metric("llm_grading_latency_s", latency)
    mlflow.log_metric("total_score", final_score)
    mlflow.log_metric("max_possible_score", max_score)
    
    # Model info
    mlflow.log_param("trocr_model_version", TROCR_VERSION)
    mlflow.log_param("llm_model_version", LLM_VERSION)
    mlflow.log_param("paper_type", paper_type)
    
    # Artifacts
    mlflow.log_artifact(answer_sheet_path)
    mlflow.log_dict(grading_result, "grading_result.json")
```

### Model Versioning with MLflow Model Registry

```
Model Registry:
├── TrOCR-Handwritten
│   ├── Version 1: microsoft/trocr-base-handwritten  [Production]
│   └── Version 2: fine-tuned on domain data         [Staging]
└── Mistral-Grader
    ├── Version 1: Mistral-7B-Instruct-v0.3           [Production]
    └── Version 2: fine-tuned on graded samples       [Staging]
```

**Promotion workflow:**
1. New model version evaluated on held-out test set
2. If accuracy > current Production: promote to Production via MLflow API
3. Backend reads active Production version tag at startup

### DVC for Data Versioning
```bash
dvc init
dvc add data/answer_keys/
dvc add models/trocr_finetuned/
git tag v1.0-dataset
```

---

## 7. Step-by-Step Implementation Plan

### Phase 0 — Project Setup (Day 1–2)
- [ ] Create monorepo: `evalify/frontend/`, `evalify/backend/`, `evalify/ml/`, `evalify/k8s/`
- [ ] Initialize `git` + `.gitignore` + `DVC`
- [ ] Create `teacher_credentials.env` and `student_credentials.env`
- [ ] Set up MongoDB locally (Docker single container)
- [ ] Set up MLflow tracking server (Docker single container)
- [ ] Write base `docker-compose.dev.yml` for local development

---

### Phase 1 — Frontend Shell (Day 2–4)
- [ ] Scaffold React + Vite + TailwindCSS
- [ ] Set up React Router v6 with route guards (auth check)
- [ ] Build layout components: `Navbar`, `Sidebar`, `Card`, `Button`, `Modal`
- [ ] Build auth pages: `TeacherLogin`, `StudentLogin`
- [ ] Build teacher pages (mock data):
  - `TeacherDashboard` — list of created papers
  - `CreatePaper` — multi-step wizard (Step 1–5)
  - `PaperResults` — result table per paper
- [ ] Build student pages (mock data):
  - `StudentDashboard` — subject cards
  - `SubjectPage` — available papers
  - `SubmissionPage` — upload answer sheet
  - `ResultPage` — name, roll, marks, avg, highest
- [ ] Connect all pages with React Router
- [ ] Add loading skeletons and success modals
- [ ] **Test:** Full UI flow works with mock data

---

### Phase 2 — Backend Foundation (Day 4–6)
- [ ] Scaffold FastAPI app with routers: `/auth`, `/papers`, `/submissions`, `/results`
- [ ] Connect MongoDB with Motor (async)
- [ ] Implement JWT auth (HS256) with `.env` credentials
- [ ] Implement `/auth/teacher/login` and `/auth/student/login`
- [ ] Implement CRUD for papers: `POST /papers`, `GET /papers`, `GET /papers/{id}`
- [ ] Implement `POST /submissions` (store file + metadata)
- [ ] Implement `GET /results/{student_id}`
- [ ] Add CORS middleware for React dev server
- [ ] Write Pytest tests for all endpoints
- [ ] **Test:** Frontend ↔ Backend communication verified (Green Signal #1)

---

### Phase 3 — Type 1 MCQ Evaluation (Day 6–10)
**This is the first ML component. Verify fully before proceeding.**

- [ ] Build OMR service (`ml/omr_service.py`):
  - Deskew + threshold pipeline with OpenCV
  - Bubble grid detection (configurable rows × 4 columns for A/B/C/D)
  - Answer extraction → JSON `{Q1: "A", Q2: "C", ...}`
- [ ] Build TrOCR service (`ml/trocr_service.py`):
  - Load `microsoft/trocr-base-handwritten`
  - Image → text pipeline
  - Parse MCQ answer pattern from text
- [ ] Expose as internal FastAPI sub-services (port 8001, 8002)
- [ ] Wire `POST /evaluate` in main backend:
  - Route to OMR or TrOCR based on `sheet_type` field
  - Compare with stored answer key
  - Compute score, store in MongoDB
  - Log metrics to MLflow
- [ ] Frontend: connect SubmissionPage to real API
- [ ] **Test:** Upload real MCQ OMR → correct score returned (Green Signal #2)

---

### Phase 4 — Type 2 MCQ + Numerical (Day 10–14)
- [ ] Extend TrOCR pipeline to segment MCQ vs Numerical sections
- [ ] Implement numerical tolerance grader (`ml/numerical_grader.py`)
- [ ] Extend teacher paper-creation UI: add per-numerical-question tolerance fields
- [ ] Extend `/evaluate` to handle Type 2 logic
- [ ] **Test:** Upload Type 2 sheet → MCQ + numerical both graded correctly (Green Signal #3)

---

### Phase 5 — Type 3 MCQ + Numerical + Subjective (Day 14–20)
- [ ] Set up Mistral 7B on V100 server:
  - Use `vllm` for OpenAI-compatible serving: `vllm serve mistralai/Mistral-7B-Instruct-v0.3`
  - Expose on port 8003 (internal only)
- [ ] Implement LLM grading service (`ml/llm_grader.py`) with prompt template from Section 5
- [ ] Extend teacher UI: rubric input per subjective question
- [ ] Extend TrOCR pipeline: isolate subjective section text
- [ ] Wire full Type 3 pipeline in `/evaluate`
- [ ] Add MLflow logging for LLM latency + scores
- [ ] **Test:** Full Type 3 submission → correct composite score (Green Signal #4)

---

### Phase 6 — Docker Containerization (Day 20–23)
- [ ] Write `Dockerfile` for each service (multi-stage builds for small images):
  - `frontend` — Node build → Nginx static serve (~25MB)
  - `backend` — Python 3.11 slim + FastAPI (~400MB)
  - `omr-service` — Python + OpenCV (~600MB)
  - `trocr-service` — Python + transformers + model weights (~2GB)
  - `llm-service` — vLLM + Mistral 7B (~15GB, runs on V100)
  - `mongodb` — official mongo:7 image
  - `mlflow` — official mlflow image
- [ ] Write `docker-compose.prod.yml`
- [ ] Test full stack with `docker-compose up`
- [ ] **Test:** All services healthy, end-to-end flow works in Docker

---

### Phase 7 — Kubernetes (Day 23–28)
- [ ] Write K8s manifests in `k8s/`:
  ```
  k8s/
  ├── namespace.yaml
  ├── configmaps/          # env vars
  ├── secrets/             # credentials (base64)
  ├── deployments/         # one per service
  ├── services/            # ClusterIP for internal, NodePort/LB for external
  ├── ingress.yaml         # Nginx ingress controller
  ├── pvc.yaml             # MongoDB + MLflow persistent volumes
  └── hpa.yaml             # Horizontal Pod Autoscaler for backend
  ```
- [ ] GPU scheduling for LLM service:
  ```yaml
  resources:
    limits:
      nvidia.com/gpu: "1"
  ```
- [ ] Deploy to server cluster: `kubectl apply -f k8s/`
- [ ] Verify all pods running: `kubectl get pods -n evalify`
- [ ] Set up Ingress with domain or IP routing

---

### Phase 8 — Deployment (Day 28–30)
- [ ] **Frontend:** Deploy to Hugging Face Spaces (static React build)
  - Update API base URL to point to server IP
- [ ] **Backend + ML Services:** Run on V100 server via K8s
- [ ] Configure TLS (cert-manager or manual cert)
- [ ] Final end-to-end test on production URLs
- [ ] Write README with setup and usage instructions

---

## 8. Docker & Kubernetes Strategy

### Keeping Images Lightweight

```dockerfile
# Frontend — multi-stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Final image: ~25MB
```

```dockerfile
# Backend — slim Python
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Resource Allocation in K8s

| Service | CPU Request | Memory Request | GPU |
|---------|------------|----------------|-----|
| frontend | 100m | 128Mi | — |
| backend | 500m | 512Mi | — |
| omr-service | 200m | 256Mi | — |
| trocr-service | 1000m | 2Gi | optional |
| llm-service | 4000m | 16Gi | 1× V100 |
| mongodb | 500m | 1Gi | — |
| mlflow | 200m | 512Mi | — |

### HPA for Backend
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 9. Deployment Strategy

```
Internet
    │
    ▼
Nginx Ingress (K8s)
    ├── /          → frontend service (or HF Spaces static)
    ├── /api       → backend service (FastAPI)
    ├── /mlflow    → mlflow UI (internal/admin only)
    └── /ws        → websocket (future: real-time evaluation progress)

V100 Server (on-premise)
    └── K8s cluster with GPU node pool
        ├── llm-service pod     (GPU: V100 #1)
        ├── trocr-service pod   (GPU: V100 #2 or CPU)
        └── remaining pods      (CPU)
```

**Hugging Face Spaces deployment for frontend:**
- Spaces supports static HTML/JS — just upload the `dist/` folder
- Set `VITE_API_BASE_URL` to your server's public IP/domain at build time

---

## 10. Directory Structure

```
evalify/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── auth/          TeacherLogin.jsx, StudentLogin.jsx
│   │   │   ├── teacher/       Dashboard.jsx, CreatePaper.jsx, PaperResults.jsx
│   │   │   └── student/       Dashboard.jsx, SubjectPage.jsx, Submission.jsx, Result.jsx
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
│   │   ├── models/            paper.py, submission.py, user.py, result.py
│   │   ├── services/          omr_client.py, trocr_client.py, llm_client.py
│   │   ├── db/                mongodb.py, mlflow_logger.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml/
│   ├── omr_service/           app.py, detector.py, Dockerfile
│   ├── trocr_service/         app.py, ocr.py, parser.py, Dockerfile
│   └── llm_service/           app.py, grader.py, prompts.py, Dockerfile
│
├── k8s/
│   ├── namespace.yaml
│   ├── deployments/
│   ├── services/
│   ├── ingress.yaml
│   ├── pvc.yaml
│   └── hpa.yaml
│
├── mlflow/
│   └── docker-compose.mlflow.yml
│
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── teacher_credentials.env
├── student_credentials.env
└── EVALIFY_PLAN.md
```

---

## 11. API Contract

### Auth
```
POST /api/auth/teacher/login    { email, password } → { token, teacher_id }
POST /api/auth/student/login    { roll_no, password } → { token, student_id }
```

### Papers (Teacher)
```
POST   /api/papers              Create paper (multipart: metadata + files)
GET    /api/papers              List all papers (teacher's)
GET    /api/papers/{id}         Get paper detail
DELETE /api/papers/{id}         Delete paper
```

### Submissions (Student)
```
GET    /api/papers/available    Papers available to student (by subject)
POST   /api/submissions         Upload answer sheet (multipart)
GET    /api/submissions/{id}/status   Evaluation status (pending/processing/done)
```

### Results
```
GET    /api/results/{submission_id}     Individual result
GET    /api/results/paper/{paper_id}    All results for a paper (teacher view)
```

### ML Services (internal, not exposed to frontend)
```
POST   :8001/omr/detect         image → {Q1: "A", Q2: "B", ...}
POST   :8002/trocr/extract      image → {text, confidence, sections}
POST   :8003/llm/grade          {question, rubric, student_answer} → {score, feedback}
```

---

## 12. Updated Prompt for Code Generation

Use the following consolidated prompt when generating code with an AI assistant:

---

```
Build "Evalify" — an Automated Handwritten Answer Sheet Evaluation System.

## Stack
- Frontend: React 18 + Vite + TailwindCSS + React Router v6 + Axios + React Query + Zustand
- Backend: FastAPI (Python 3.11) + Motor (async MongoDB) + PyJWT
- Database: MongoDB (document model justified by variable paper-type schemas)
- ML services: OpenCV (OMR), TrOCR (OCR), Mistral-7B via vLLM (LLM grading)
- MLOps: MLflow for experiment tracking + model registry
- Infrastructure: Docker (multi-stage, lightweight) + Kubernetes (with GPU scheduling)

## Roles
- Teacher: create papers, upload answer keys + rubrics, view all results
- Student: login, view exams by subject, upload answer sheet, view results

## Paper Types
1. MCQ Only
   - Sub-type A: OMR sheet → OpenCV bubble detection
   - Sub-type B: Normal written → TrOCR OCR + regex answer parsing
2. MCQ + Numerical
   - TrOCR for both sections
   - Numerical grading: tolerance-based (range, exact, decimal_variants)
   - Teacher specifies tolerance per numerical question
3. MCQ + Numerical + Subjective
   - TrOCR for MCQ + Numerical sections
   - TrOCR for subjective section → text extracted
   - LLM (Mistral 7B) grades subjective using structured rubric
   - Prompt: low temperature (0.1), JSON-only response, concept-based scoring
   - MLflow logs LLM latency, scores, model version per evaluation run

## Teacher Create Paper Flow (5 Steps)
1. Select paper type (MCQ / MCQ+Numerical / MCQ+Numerical+Subjective)
2. Upload question paper image → mock: simulate extracting N questions → input marks/question
3. Upload answer key (image or manual input)
4. Additional info:
   - MCQ: optional (negative marking toggle)
   - MCQ+Numerical: mandatory tolerance config per numerical question
   - MCQ+Numerical+Subjective: mandatory rubric per subjective question
     (key_concepts[], mandatory_concepts[], marks_per_concept, model_answer)
5. Save → success modal "You have successfully created an exam evaluation"

## Student Flow
1. Login → Dashboard (subject cards) → Subject page (available papers)
2. Upload scanned answer sheet → polling for evaluation status
3. Result page: Name, Roll No, Marks Obtained, Average Marks, Highest Marks

## UI Requirements
- Clean, minimal, modern design — light theme
- Rounded cards, soft shadows, consistent spacing
- TailwindCSS utility classes only
- Loading skeletons (not spinners) for async states
- Success/error toasts + modal popups
- Fully responsive (mobile + desktop)

## Implementation Order (test each before proceeding)
Phase 1: Frontend shell with mock data (all pages + routing)
Phase 2: Backend API + MongoDB + JWT auth (Green Signal: API communication works)
Phase 3: Type 1 MCQ evaluation with OMR + TrOCR (Green Signal: real scoring works)
Phase 4: Type 2 MCQ+Numerical with tolerance grading
Phase 5: Type 3 subjective with LLM grading + MLflow logging
Phase 6: Docker containerization (multi-stage, lightweight)
Phase 7: Kubernetes manifests with GPU scheduling for LLM service
Phase 8: Deploy frontend to Hugging Face Spaces, backend on V100 server

## Code Requirements
- Modular: one component per file, one router per domain
- No ML logic in Phase 1/2 — simulate with mock data and setTimeout
- Auth: JWT stored in memory (not localStorage) for security
- All API calls through a single Axios instance with auth interceptor
- Environment variables for all URLs and secrets (never hardcoded)
- Dockerfile per service, docker-compose.dev.yml for local dev

## DO NOT implement yet
- Actual OCR inference
- Actual LLM calls
- Fine-tuning pipelines
Simulate these with mock functions that return plausible fake data after a 2s delay.
```

---

## Green Signal Checklist

| Signal | Condition | Phase |
|--------|-----------|-------|
| #1 | All UI pages render, navigation works, mock data displays | Phase 1 |
| #2 | Frontend ↔ Backend API works, auth flow complete, papers saved to MongoDB | Phase 2 |
| #3 | Type 1 MCQ sheet uploaded → real score returned via OMR/TrOCR | Phase 3 |
| #4 | Type 2 sheet → MCQ + numerical both graded with tolerance | Phase 4 |
| #5 | Type 3 sheet → LLM grades subjective, MLflow logs run | Phase 5 |
| #6 | All services run in Docker, docker-compose up works | Phase 6 |
| #7 | K8s cluster healthy, GPU pod running LLM service | Phase 7 |
| #8 | Live URL accessible, end-to-end flow on production | Phase 8 |

---

*Last updated: April 20, 2026*
