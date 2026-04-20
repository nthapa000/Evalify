# Backend Dockerfile — Python 3.11 slim image.
# Phase 0: builds the base image; ML dependencies added in Phase 3+.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by some Python packages (e.g. bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies before copying source code.
# This layer is cached as long as requirements.txt doesn't change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Uvicorn serves the FastAPI app; bind to 0.0.0.0 so K8s can route to it
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
