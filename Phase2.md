# Phase 2 — Backend Foundation

## Goal
Build the complete FastAPI backend with MongoDB (Motor async), JWT authentication, CRUD endpoints for papers/submissions/results, and wire the frontend to use real API calls. This establishes the API communication path between the React SPA and the Python backend — **Green Signal #2**.

---

## What Was Done in Phase 2

| Area | Files Created / Modified |
|------|-----------------------------|
| Config | `config.py` — pydantic-settings loading from `.env` |
| Database | `db/mongodb.py` — Motor async connect/disconnect + collection helpers |
| Seed | `db/seed.py` — Idempotent bcrypt-hashed user seeder |
| Models | `models/user.py`, `models/paper.py`, `models/submission.py` |
| Auth Router | `routers/auth.py` — JWT login + `get_current_user` dependency |
| Papers Router | `routers/papers.py` — CRUD + available-for-student |
| Submissions Router | `routers/submissions.py` — Upload + mock evaluation + polling |
| Results Router | `routers/results.py` — Individual + paper-level results |
| Main App | `main.py` — Lifespan, router registration, CORS |
| Frontend | `api.js` — Wired Zustand authStore token into Axios interceptor |
| Tests | `tests/conftest.py`, `tests/test_auth.py`, `tests/test_papers.py` |
| Packages | `__init__.py` in `app/`, `app/routers/`, `app/models/`, `app/db/`, `app/services/`, `tests/` |

**Total: 17 new files · 1 modified file**

---

## System Flow Diagram — Phase 2

```
┌─────────────────────────────────────────────────────────────────────┐
│                      BROWSER (React SPA :5173)                       │
│                                                                      │
│  useAuth.loginTeacher()  ──► POST /api/auth/teacher/login            │
│  useAuth.loginStudent()  ──► POST /api/auth/student/login            │
│  usePapers.createPaper() ──► POST /api/papers                        │
│  usePapers.listPapers()  ──► GET  /api/papers                        │
│  useSubmission.submit()  ──► POST /api/submissions?paper_id=xxx      │
│  useSubmission.poll()    ──► GET  /api/submissions/{id}/status       │
│  useResult.getResult()   ──► GET  /api/results/{submission_id}       │
│                                                                      │
│  Axios interceptor: Authorization: Bearer <JWT from Zustand store>   │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  HTTP REST (JSON)
                                │  Vite proxy: /api → localhost:30000
┌───────────────────────────────▼──────────────────────────────────────┐
│                    BACKEND (FastAPI :30000)                            │
│                                                                      │
│  Lifespan:                                                           │
│    startup  → connect_db() → seed_users()                            │
│    shutdown → close_db()                                             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  /api/auth/*          JWT login (bcrypt verify + HS256 sign) │    │
│  │  /api/papers/*        CRUD (teacher creates, student reads)  │    │
│  │  /api/submissions/*   Upload + mock eval (4s delay)          │    │
│  │  /api/results/*       Individual + paper-level results       │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  get_current_user()   ← Decodes JWT, returns user payload    │    │
│  │  require_teacher()    ← Ensures role == "teacher"            │    │
│  │  require_student()    ← Ensures role == "student"            │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                         │                                            │
│                ┌────────▼──────────┐                                 │
│                │  MongoDB :27017   │                                  │
│                │  evalify_db       │                                  │
│                │  ┌──────────────┐ │                                  │
│                │  │ users        │ │  email/roll_no index             │
│                │  │ papers       │ │  teacher_id index                │
│                │  │ submissions  │ │  student_id + paper_id index     │
│                │  │ results      │ │  submission_id index             │
│                │  └──────────────┘ │                                  │
│                └───────────────────┘                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow

```
Teacher Login:
  email + password
      │
      ▼
  POST /api/auth/teacher/login
      │
      ├── users_col.find_one({ email, role:"teacher" })
      ├── bcrypt.verify(password, stored_hash)
      ├── jwt.encode({ sub: user_id, role: "teacher" }, TEACHER_SECRET)
      │
      ▼
  { token: "eyJ...", user: { id, name, email, role } }
      │
      ▼
  authStore.setAuth(token, user)  ← stored in Zustand (memory only)
      │
      ▼
  Axios interceptor auto-attaches: Authorization: Bearer <token>
```

---

## Submission & Evaluation Flow (Mock — Phase 2)

```
Student uploads answer sheet
      │
      ▼
  POST /api/submissions?paper_id=xxx
      │
      ├── Create submission doc { status: "processing" }
      ├── asyncio.create_task( mock_evaluation(4s delay) )
      │
      ▼
  Return { id: "sub_id", status: "processing" }
      │
      ▼
  Frontend polls: GET /api/submissions/{id}/status  (every 2s)
      │
      ├── status: "processing" → keep polling
      ├── status: "evaluated"  → redirect to result page
      │
  (after 4s) Mock evaluation runs:
      ├── Generate random score
      ├── Update submission: status="evaluated", result={...}
      │
      ▼
  GET /api/results/{submission_id}
      └── Returns score + peer stats (avg, highest)
```

---

## File-by-File Purpose

### `backend/app/config.py`
Loads all configuration from `teacher_credentials.env` and `student_credentials.env` via `pydantic-settings`. Contains MongoDB URI, JWT secrets, expiration times, and seed credentials. Exported as a singleton `settings` object.

### `backend/app/db/mongodb.py`
Motor async client wrapper. `connect_db()` opens the connection and verifies with a ping; `close_db()` cleans up. Provides `get_db()` for the database handle and shortcut functions (`users_col()`, `papers_col()`, etc.) for each collection.

### `backend/app/db/seed.py`
Inserts a default teacher and student with real bcrypt password hashes. Idempotent — checks if users already exist before inserting. Called automatically during app startup via the lifespan handler.

### `backend/app/models/user.py`
Pydantic schemas: `TeacherLoginRequest` (email + password), `StudentLoginRequest` (roll_no + password), `LoginResponse` (token + user dict), and `UserOut` (safe user without password hash).

### `backend/app/models/paper.py`
Pydantic schemas: `PaperCreate` (full paper creation payload including MCQ/numerical/subjective fields, per-question marks maps, and PDF URLs), `PaperOut` (full response), and `PaperListItem` (lightweight dashboard summary).

### `backend/app/models/submission.py`
Pydantic schemas: `SubmissionOut` (full submission), `SubmissionStatusOut` (status polling), and `ResultOut` (full result with peer stats and paper context).

### `backend/app/routers/auth.py`
JWT authentication router. Two login endpoints (teacher by email, student by roll_no). Password verification via bcrypt. Token creation via PyJWT (HS256). Three FastAPI dependencies: `get_current_user` (decode any token), `require_teacher`, `require_student` (role guards).

### `backend/app/routers/papers.py`
Paper CRUD router. Create (teacher only), list (teacher's papers with result counts), get single paper, list available papers (for students, with submission status overlay), and delete (teacher only, ownership check).

### `backend/app/routers/submissions.py`
Submission router. POST creates a "processing" submission and fires an `asyncio.create_task` for mock evaluation (4s delay, random score). GET status polls the latest status. In Phase 3+, the mock evaluation will be replaced with real ML pipeline calls.

### `backend/app/routers/results.py`
Results router. GET individual result (with peer stats: average, highest). GET paper-level results (teacher view: all evaluated submissions + aggregate stats).

### `backend/app/main.py`
FastAPI application entry-point. Uses the `lifespan` async context manager for MongoDB connect/disconnect and seed. Registers all four routers under `/api` prefix. CORS configured for the React dev server at port 5173.

### `frontend/src/services/api.js`
Updated Axios interceptor to read the JWT from `useAuthStore.getState().token` instead of the placeholder `window.__evalify_token__`. This means all API calls automatically include the auth header once the user logs in.

---

## How to Start Phase 2 Dev Environment

```bash
# 1. Start MongoDB (from project root)
docker compose -f docker-compose.dev.yml up -d mongodb

# 2. Start FastAPI backend (new terminal)
cd backend
python3.11 -m venv venv          # one-time
source venv/bin/activate
pip install -r requirements.txt  # one-time
uvicorn app.main:app --reload --port 30000

# 3. Start React frontend (another terminal)
cd frontend
npm run dev
# → http://localhost:5173

# Teacher demo:  teacher@evalify.local / Teacher@123
# Student demo:  CS2025001 / Student@123
```

---

## Phase Checklist

| Phase | Status |
|-------|--------|
| **Phase 0** | ✅ Done |
| **Phase 1** | ✅ Done |
| **Phase 2** | ✅ Done |
| Phase 3 | Type 1 MCQ evaluation (OMR + TrOCR) |
| Phase 4 | Type 2 MCQ + Numerical (tolerance grading) |
| Phase 5 | Type 3 Subjective + LLM + MLflow |
| Phase 6 | Docker containerisation |
| Phase 7 | Kubernetes deployment |
| Phase 8 | Production deploy |
