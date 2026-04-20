# main.py — FastAPI application entry-point.
# Registers all routers, configures CORS, and manages MongoDB lifecycle.

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Database lifecycle hooks
from app.db.mongodb import connect_db, close_db
from app.db.seed import seed_users

# Routers (one per domain)
from app.routers import auth, papers, submissions, results


# ── Lifespan: connect to Mongo on startup, disconnect on shutdown ────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup (before yield) and shutdown (after yield)."""
    await connect_db()     # open Motor client
    await seed_users()     # insert seed teacher + student if missing
    yield
    await close_db()       # close Motor client


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
