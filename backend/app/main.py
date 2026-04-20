# main.py — FastAPI application entry-point.
# Phase 0: bare app with CORS. Routers will be registered in Phase 2.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Evalify API",
    version="0.1.0",
    description="Automated Handwritten Answer Sheet Evaluation System",
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


@app.get("/health")
async def health():
    # Kubernetes liveness probe hits this endpoint
    return {"status": "ok", "service": "evalify-backend"}
