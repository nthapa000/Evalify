#!/bin/bash
# start.sh — Start Evalify backend (venv uvicorn) + Ollama vision server.
# Run from the backend/ directory: bash start.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
VENV_UVICORN="$SCRIPT_DIR/venv/bin/uvicorn"
OLLAMA_BIN="$HOME/.local/bin/ollama"

if [ ! -f "$VENV_PYTHON" ]; then
  echo "❌ venv not found at $SCRIPT_DIR/venv — run: python3.11 -m venv venv && pip install -r requirements.txt"
  exit 1
fi

echo "✅ Using Python: $($VENV_PYTHON --version)"
echo "🔦 torch: $($VENV_PYTHON -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'NOT FOUND')"
echo "🤖 GPU: $($VENV_PYTHON -c 'import torch; print("CUDA" if torch.cuda.is_available() else "CPU")' 2>/dev/null || echo 'N/A')"
echo ""

# ── Start Ollama if not already running ──────────────────────────────────────
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "✅ Ollama: already running at localhost:11434"
else
  if [ -f "$OLLAMA_BIN" ]; then
    echo "🚀 Ollama: starting server …"
    export OLLAMA_MODELS="$HOME/.ollama/models"
    # GPU libraries live at ~/.local/lib/ollama/ (copied from release tarball).
    # System libnvidia-ml.so.1 is in /usr/lib64 — needed for GPU detection.
    export LD_LIBRARY_PATH="/usr/lib64:/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    unset CUDA_VISIBLE_DEVICES
    "$OLLAMA_BIN" serve >> "$SCRIPT_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    echo "   PID=$OLLAMA_PID, log → backend/ollama.log"
    sleep 4
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
      echo "✅ Ollama: ready"
    else
      echo "⚠️  Ollama: did not start — handwritten OCR will run in STUB mode"
    fi
  else
    echo "⚠️  Ollama binary not found at $OLLAMA_BIN — handwritten OCR will run in STUB mode"
  fi
fi

echo ""
cd "$SCRIPT_DIR"
exec "$VENV_UVICORN" app.main:app --host 0.0.0.0 --port 47823 --reload 2>&1 | tee backend.log
