# main.py — FastAPI entry point: routers, CORS, MongoDB lifecycle.

import os
from contextlib import asynccontextmanager

# passlib 1.7.4 reads bcrypt.__about__, removed in bcrypt 4.x — patch before passlib loads
import bcrypt as _bcrypt
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = type("_about", (), {"__version__": _bcrypt.__version__})()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db.mongodb import close_db, connect_db
from app.db.seed import seed_users
from app.routers import auth, papers, results, submissions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect + seed MongoDB on startup, close on shutdown."""
    await connect_db()
    await seed_users()
    yield
    await close_db()


async def log_validation_error(request: Request, exc: RequestValidationError):
    """Print 422 details (helps debug frontend payloads) and return them."""
    print(f"❌ 422 on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# App instance
app = FastAPI(title="Evalify API", version="0.3.0",
              description="Automated Handwritten Answer Sheet Evaluation System",
              lifespan=lifespan,
              exception_handlers={RequestValidationError: log_validation_error})

# CORS: comma-separated origins from CORS_ORIGINS (defaults cover Vite + nginx)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost").split(",") if o.strip()],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# All routes live under /api (matches the frontend's Axios baseURL)
for r in (auth, papers, submissions, results):
    app.include_router(r.router, prefix="/api")


@app.get("/api/health")
async def health():
    """Liveness probe."""
    return {"status": "ok", "service": "evalify-backend", "version": "0.3.0"}
