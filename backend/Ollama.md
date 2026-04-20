# Ollama Setup & Usage Guide — Evalify

This document explains how Ollama is installed, configured, and used in Evalify.
It covers every step from a fresh machine, which models are used and why, and how
to run Ollama both locally and on a shared server.

---

## Table of Contents
1. [What is Ollama?](#1-what-is-ollama)
2. [Installation (no sudo / user-space)](#2-installation-no-sudo--user-space)
3. [Starting the Ollama Server](#3-starting-the-ollama-server)
4. [Models Used in Evalify](#4-models-used-in-evalify)
5. [Pulling a Model](#5-pulling-a-model)
6. [How Evalify Calls Ollama](#6-how-evalify-calls-ollama)
7. [Running on a Shared DGX Server](#7-running-on-a-shared-dgx-server)
8. [Environment Variables](#8-environment-variables)
9. [Troubleshooting](#9-troubleshooting)
10. [Future Use: Subjective Answer Evaluation](#10-future-use-subjective-answer-evaluation)

---

## 1. What is Ollama?

Ollama is a lightweight server that downloads and serves open-source LLMs locally
via a REST API. It manages model weights, GPU memory, and inference — your Python
code just calls `http://localhost:11434/api/generate`.

Why we use it instead of loading models directly in Python:
- **One process, many use cases** — same server handles handwritten OCR, subjective grading, etc.
- **No Python ML dependency conflicts** — your FastAPI app only needs `requests`
- **Easy model swap** — change the model name in an env var, no code changes
- **Docker/deployment friendly** — Ollama runs as a standalone service

---

## 2. Installation (no sudo / user-space)

> **Critical:** The Ollama tarball contains GPU acceleration libraries
> (`lib/ollama/cuda_v12/`, `lib/ollama/libggml-base.so`, etc.) that **must**
> be copied alongside the binary. If you only copy the binary, Ollama silently
> falls back to CPU — inference of an 11B model then takes ~90 seconds per
> request and will timeout. Always follow step 4 below.


On a shared server where you don't have root access, install the Ollama binary to
your home directory:

```bash
# Step 1: Create a local bin directory (if it doesn't exist)
mkdir -p ~/.local/bin

# Step 2: Find the latest release tag
curl -s https://api.github.com/repos/ollama/ollama/releases/latest \
  | grep '"tag_name"' | head -1
# Example output: "tag_name": "v0.21.0"

# Step 3: Download the Linux AMD64 tarball
curl -fsSL https://github.com/ollama/ollama/releases/download/v0.21.0/ollama-linux-amd64.tar.zst \
  -o /tmp/ollama.tar.zst

# Step 4: Extract the binary
cd /tmp && tar --use-compress-program=unzstd -xf ollama.tar.zst

# Step 5: Copy the binary to your local bin
cp /tmp/bin/ollama ~/.local/bin/ollama
chmod +x ~/.local/bin/ollama

# Step 6: Copy GPU acceleration libraries (REQUIRED for GPU inference)
mkdir -p ~/.local/lib/ollama
cp -r /tmp/lib/ollama/* ~/.local/lib/ollama/
# This copies: cuda_v12/, cuda_v13/, libggml-base.so, libggml-cpu-*.so, etc.
# Ollama looks for libs at <binary_dir>/../lib/ollama — so ~/.local/bin → ~/.local/lib/ollama

# Step 7: Verify installation
~/.local/bin/ollama --version
```

Add `~/.local/bin` to your PATH permanently by adding this to `~/.bashrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## 3. Starting the Ollama Server

### Via `bash start.sh` (recommended for Evalify)

The `backend/start.sh` script automatically checks if Ollama is running and starts
it if not:

```bash
cd /home/m25csa019/Evalify/backend
bash start.sh
```

The script:
1. Checks `http://localhost:11434/api/tags` to see if Ollama is already up
2. If not, launches `ollama serve` in the background and waits 4 seconds
3. Logs Ollama output to `backend/ollama.log`
4. Then starts the FastAPI backend on port 47823

### Manually starting Ollama

```bash
# Set where model weights are stored (default: ~/.ollama/models)
export OLLAMA_MODELS=~/.ollama/models

# Start the server (runs in background)
~/.local/bin/ollama serve > ~/ollama.log 2>&1 &

# Verify it's running
curl http://localhost:11434/api/tags
# Expected: {"models": [...]}
```

### Stopping Ollama

```bash
pkill -f "ollama serve"
```

---

## 4. Models Used in Evalify

### `llama3.2-vision:11b` — Primary model

| Property        | Value                              |
|-----------------|------------------------------------|
| Parameters      | 11 billion                         |
| VRAM (4-bit)    | ~8 GB                              |
| Context window  | 128k tokens                        |
| Capabilities    | Text + Image understanding (VLM)   |
| Use in Evalify  | Handwritten MCQ extraction, future subjective grading |

**Why this model?**

We evaluated three approaches for handwritten MCQ answer extraction:

1. **TrOCR (microsoft/trocr-base-handwritten)** — Tried first. Trained on the IAM
   dataset (full English sentences). When given MCQ answer sheets with patterns like
   `"1. A"`, it hallucinates fluent English sentences. Rejected.

2. **EasyOCR** — Better character detection but low confidence (~0.36 avg) on
   handwritten single-letter answers. Cannot understand context (e.g. telling Q4
   from Q14 when handwriting is unclear). Rejected.

3. **llama3.2-vision:11b via Ollama** — A vision-language model (VLM) that
   *understands* the image contextually. Given the question count in the prompt,
   it knows the valid range of keys and will not invent question numbers beyond
   the paper's scope. Selected.

**Hardware fit:** Two Tesla V100-SXM3-32GB (32 GB each) on the DGX server.
`llama3.2-vision:11b` uses ~8 GB, leaving room for the PyTorch OMR engine and
other processes.

---

## 5. Pulling a Model

```bash
# Pull llama3.2-vision (11B, ~8GB download)
~/.local/bin/ollama pull llama3.2-vision:11b

# List all locally available models
~/.local/bin/ollama list

# Remove a model (to free disk space)
~/.local/bin/ollama rm llama3.2-vision:11b
```

Model weights are stored at `~/.ollama/models/` by default.

---

## 6. How Evalify Calls Ollama

Flow for a handwritten answer sheet submission:

```
Student uploads JPEG/PDF
        │
        ▼
evaluator.py  →  _extract_answers(img_path, sheet_type="handwritten", mcq_count=N)
        │
        ▼
trocr_engine.py  →  _ollama_extract(image_path, mcq_count=N)
        │
        │  builds prompt via: app/prompts/prompt_mcq.py → build_mcq_prompt(mcq_count=N)
        │
        ▼
POST http://localhost:11434/api/generate
     model: llama3.2-vision:11b
     prompt: "The paper has exactly N questions ... return JSON ..."
     images: [base64-encoded image]
        │
        ▼
Response: {"Q1": "A", "Q2": "C", "Q3": "B", ...}   ← at most N keys
        │
        ▼
parse_mcq_results()  →  try json.loads() first, fallback regex
        │
        ▼
_grade_mcq()  →  compare with answer key  →  save result to MongoDB
```

The key prompt improvement: we tell the model `mcq_count` explicitly. If the paper
has 15 questions, the model is told to return at most 15 key-value pairs (Q1–Q15).
This prevents invented entries like Q16, Q20, etc.

See [app/prompts/prompt_mcq.py](app/prompts/prompt_mcq.py) for the exact prompt template.

---

## 7. Running on a Shared DGX Server

**Port conflict awareness:** On this DGX machine, port 8000 is occupied by another
user's LLM server (lmdeploy). Evalify uses:
- FastAPI backend: port **47823**
- Ollama: port **11434** (default, confirmed free)

Check if port 11434 is in use before starting:
```bash
ss -tlnp | grep 11434
```

If 11434 is taken, use a different port:
```bash
OLLAMA_HOST=0.0.0.0:11440 ~/.local/bin/ollama serve &
```
Then set `OLLAMA_HOST=http://localhost:11440` in your environment before running
`bash start.sh`.

**GPU memory check:**
```bash
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
```
You need at least ~8 GB free on one GPU before pulling and running the model.

---

## 8. Environment Variables

| Variable              | Default                      | Purpose                          |
|-----------------------|------------------------------|----------------------------------|
| `OLLAMA_HOST`         | `http://localhost:11434`     | Ollama server URL (in FastAPI)   |
| `OLLAMA_VISION_MODEL` | `llama3.2-vision:11b`        | Model used for vision tasks      |
| `OLLAMA_MODELS`       | `~/.ollama/models`           | Where model weights are stored   |

Set them in `backend/.env` or export before running `bash start.sh`:
```bash
export OLLAMA_VISION_MODEL=llama3.2-vision:11b
bash start.sh
```

---

## 9. Troubleshooting

**"Ollama server unreachable — running in STUB mode"**
```bash
# Check if ollama serve is running
ps aux | grep ollama

# Start it manually
~/.local/bin/ollama serve > /tmp/ollama.log 2>&1 &
sleep 4 && curl http://localhost:11434/api/tags
```

**"model not found"**
```bash
# Pull the model
~/.local/bin/ollama pull llama3.2-vision:11b
~/.local/bin/ollama list   # verify it appears
```

**Inference timeout (default 120 seconds)**
Large images on the first call load the model into GPU memory (~10–30 seconds).
Subsequent calls are faster (~5–15 seconds). If it consistently times out, check
GPU memory availability with `nvidia-smi`.

**Model returns garbled JSON**
The `parse_mcq_results()` function tries `json.loads()` first and falls back to
a regex parser. Even if the model adds surrounding text like `"Here is the JSON:"`,
the regex will still extract valid `Q1: A` patterns.

**Check Ollama logs**
```bash
cat /home/m25csa019/Evalify/backend/ollama.log
```

---

## 10. Future Use: Subjective Answer Evaluation

The same Ollama instance and model will be used for subjective question grading.
The pattern is identical — only the prompt changes:

```python
# Planned: app/prompts/prompt_subjective.py
def build_subjective_prompt(question: str, model_answer: str, student_answer: str, max_marks: int):
    return f"""You are an examiner grading a student's answer.

Question: {question}
Model Answer: {model_answer}
Student's Answer: {student_answer}
Maximum Marks: {max_marks}

Evaluate the student's answer and return ONLY a JSON object:
{{"marks": <number 0 to {max_marks}>, "feedback": "<one sentence>"}}"""
```

No new model to download, no new service to run — just a new prompt file and a
new engine method calling the same `http://localhost:11434/api/generate` endpoint.
