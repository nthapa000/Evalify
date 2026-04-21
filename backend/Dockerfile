# Backend Dockerfile — Python 3.11 slim with full ML stack.
# Build context: backend/
# Usage: docker compose -f docker-compose.dev.yml up --build backend

FROM python:3.11-slim

WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# libgl1, libglib2.0-0, libsm6, libxext6, libxrender-dev : OpenCV (cv2)
# libgomp1                                                : EasyOCR / PyTorch OpenMP
# gcc, g++, libffi-dev                                    : build tools for some wheels
# curl                                                    : healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy requirements first so this layer is cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY app/ ./app/

# Uploads directory — mounted as a named volume in docker-compose
# so files survive container restarts
RUN mkdir -p uploads/papers uploads

# ── Runtime settings ──────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1

# These defaults are overridden by docker-compose environment / env_file
ENV MONGO_URI=mongodb://evalify:evalify_dev_pass@mongodb:27017/evalify_db?authSource=admin
ENV MLFLOW_TRACKING_URI=http://mlflow:5000
# Ollama runs on the HOST with GPU — reach it via host-gateway alias
ENV OLLAMA_HOST=http://host.docker.internal:11434
ENV OLLAMA_TIMEOUT=300
ENV OLLAMA_TIMEOUT_SUBJECTIVE=180
# Comma-separated list of allowed CORS origins
ENV CORS_ORIGINS=http://localhost:5173,http://localhost

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
