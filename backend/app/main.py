# main.py — FastAPI application entry-point.
# Registers all routers, configures CORS, and manages MongoDB lifecycle.

import sys
import os
from contextlib import asynccontextmanager

# passlib 1.7.4 reads bcrypt.__about__.__version__ which was removed in bcrypt 4.x.
# Patch it before any passlib import so the "trapped error" warning is silenced.
try:
    import bcrypt as _bcrypt
    if not hasattr(_bcrypt, '__about__'):
        _bcrypt.__about__ = type('_about', (), {'__version__': _bcrypt.__version__})()
except Exception:
    pass
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ── Venv guard: warn loudly if not running from the project venv ─────────────
_VENV_PYTHON = os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python3")
_VENV_PYTHON = os.path.normpath(_VENV_PYTHON)
if not sys.executable.startswith(os.path.dirname(_VENV_PYTHON)):
    print("=" * 70)
    print("⚠️  WARNING: Backend is NOT running from the project venv!")
    print(f"   Current Python: {sys.executable}")
    print(f"   Expected venv:  {_VENV_PYTHON}")
    print("   → Ollama (GPU), MLflow, and other ML features will NOT work.")
    print("   → Run the backend with:  cd backend && bash start.sh")
    print("=" * 70)

# Database lifecycle hooks
from app.db.mongodb import connect_db, close_db
from app.db.seed import seed_users

# Routers (one per domain)
from app.routers import auth, papers, submissions, results


# ── Lifespan: connect to Mongo on startup, disconnect on shutdown ────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup (before yield) and shutdown (after yield)."""
    await connect_db()
    await seed_users()
    # Pre-import evaluator so any dependency crashes are visible at startup
    try:
        from app.services import evaluator as _ev  # noqa: F401
        print("✅ Evaluator loaded.")
    except Exception as _e:
        print(f"⚠️  Evaluator load warning: {_e}")
    yield
    await close_db()


# ── Validation error logger ───────────────────────────────────────────────────

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ 422 Validation Error on {request.method} {request.url.path}")
    print(f"   Errors: {exc.errors()}")
    body = await request.body()
    print(f"   Body: {body[:2000]}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    exception_handlers={RequestValidationError: validation_exception_handler},
    title="Evalify API",
    version="0.2.0",
    description="Automated Handwritten Answer Sheet Evaluation System",
    lifespan=lifespan,
)

# Allow the React dev server (port 5173) to reach this API during development.
# In production, replace origins with the actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers under /api prefix ────────────────────────────────────────
# This matches the frontend's Axios baseURL ("/api")

app.include_router(auth.router,        prefix="/api")
app.include_router(papers.router,      prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(results.router,     prefix="/api")


# ── Health check (used by Kubernetes liveness probes) ─────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "evalify-backend", "version": "0.2.0"}
