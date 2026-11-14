#!/usr/bin/env python3
"""serve.py — start one vLLM server per model for a serving profile and publish endpoints.

Run inside the GPU job (serve_models.sbatch). For the chosen profile in
infra/models.yaml it:
  1. checks every pinned snapshot is fully downloaded (offline afterwards);
  2. starts servers GPU by GPU — the two GPUs in parallel, servers on the same
     GPU one after another (vLLM sizes its KV cache from free memory);
  3. writes $EVALIFY_ENDPOINTS_FILE as each server becomes healthy, using the
     node's hostname so the backend on the login node can reach it;
  4. optionally runs $EVALIFY_AFTER_READY (e.g. a bake-off) once all are up;
  5. keeps running until the job ends, then stops servers and removes the file.
A server that fails to start is logged and skipped: the backend's role
fallbacks then pick another model instead of breaking.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(os.environ.get("EVALIFY_HOME", Path(__file__).resolve().parents[2]))
REG = yaml.safe_load((ROOT / "infra" / "models.yaml").read_text())
ENDPOINTS = Path(os.environ["EVALIFY_ENDPOINTS_FILE"])
LOGS = Path(os.environ["EVALIFY_LOG_DIR"])
HOST = socket.gethostname().split(".")[0]
START_TIMEOUT_S = 40 * 60          # first start compiles kernels; can be slow

procs: list[subprocess.Popen] = []
live: dict = {}
lock = threading.Lock()


def log(msg: str) -> None:
    """Timestamped line in the job log."""
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def snapshots_ready(names: set) -> list:
    """Names whose pinned revision is not fully in the HF cache."""
    from huggingface_hub import scan_cache_dir
    have = {(r.repo_id, rev.commit_hash) for r in scan_cache_dir().repos for rev in r.revisions}
    blobs = Path(os.environ["HF_HUB_CACHE"]) / "blobs"
    partial = any(blobs.rglob("*.incomplete")) if blobs.exists() else False
    missing = [n for n in names if (REG["models"][n]["repo"], REG["models"][n]["revision"]) not in have]
    return missing + (["<downloads still in progress>"] if partial else [])


def publish() -> None:
    """Atomically rewrite the endpoints file with the servers that are healthy now."""
    with lock:
        tmp = ENDPOINTS.with_suffix(".tmp")
        tmp.write_text(json.dumps({"node": HOST, "job_id": os.environ.get("SLURM_JOB_ID"),
                                   "profile": PROFILE, "updated": time.strftime("%F %T"),
                                   "models": live}, indent=2))
        tmp.replace(ENDPOINTS)


def start_gpu(gpu: str, servers: list) -> None:
    """Start this GPU's servers one at a time; each must be healthy before the next."""
    for s in servers:
        name, port, m = s["model"], s["port"], REG["models"][s["model"]]
        cmd = ["vllm", "serve", m["repo"], "--revision", m["revision"], "--served-model-name", name,
               "--host", "0.0.0.0", "--port", str(port), "--gpu-memory-utilization", str(s["mem"]),
               *[str(a) for a in m.get("vllm_args", [])]]
        log(f"GPU {gpu}: starting {name} on :{port}")
        # Profile GPU 0/1 → the i-th device Slurm allocated to this job
        device = os.environ.get("CUDA_VISIBLE_DEVICES", "0,1").split(",")[int(gpu)]
        p = subprocess.Popen(cmd, env={**os.environ, "CUDA_VISIBLE_DEVICES": device},
                             stdout=open(LOGS / f"{name}.log", "w"), stderr=subprocess.STDOUT)
        procs.append(p)

        # Poll /health until up, the process dies, or we time out
        t0 = time.time()
        while time.time() - t0 < START_TIMEOUT_S and p.poll() is None:
            try:
                if requests.get(f"http://localhost:{port}/health", timeout=2).ok:
                    break
            except requests.RequestException:
                pass
            time.sleep(10)
        else:
            log(f"GPU {gpu}: ✗ {name} failed to start (see {LOGS / (name + '.log')}); skipping")
            p.terminate()
            continue

        with lock:
            live[name] = {"base_url": f"http://{HOST}:{port}/v1", "gpu": gpu,
                          "repo": m["repo"], "revision": m["revision"]}
        publish()
        log(f"GPU {gpu}: ✓ {name} ready in {time.time() - t0:.0f}s")


def shutdown(*_) -> None:
    """Stop all servers and withdraw the endpoints file."""
    log("shutting down servers")
    for p in procs:
        p.terminate()
    ENDPOINTS.unlink(missing_ok=True)
    sys.exit(0)


if __name__ == "__main__":
    PROFILE = sys.argv[1] if len(sys.argv) > 1 else "tier1-bakeoff"
    if PROFILE not in REG["profiles"]:
        sys.exit(f"unknown profile {PROFILE!r}; choose from {list(REG['profiles'])}")
    gpus = REG["profiles"][PROFILE]["gpus"]
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # 1. All weights present? (downloads happen on the login node, never here)
    while missing := snapshots_ready({s["model"] for ss in gpus.values() for s in ss}):
        log(f"waiting for downloads: {missing}")
        time.sleep(60)

    # 2–3. Both GPUs in parallel; endpoints file grows as servers come up
    ENDPOINTS.unlink(missing_ok=True)
    threads = [threading.Thread(target=start_gpu, args=(str(g), ss)) for g, ss in gpus.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log(f"profile {PROFILE}: {len(live)} server(s) up: {sorted(live)}")

    # 4. Optional work inside the same job (keeps a Slurm slot free)
    after = os.environ.get("EVALIFY_AFTER_READY")
    if after:
        log(f"running: {after}")
        subprocess.run(after, shell=True, cwd=ROOT)

    # 5. Stay alive; exit if every server has died
    while any(p.poll() is None for p in procs):
        time.sleep(30)
    log("all servers exited")
    ENDPOINTS.unlink(missing_ok=True)
