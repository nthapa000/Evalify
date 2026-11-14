#!/usr/bin/env python3
"""download_models.py — staged, pinned model downloads into $HF_HOME on /scratch.

Usage (login node, after `source infra/cluster/env.sh`):
    python download_models.py --stage 1            # build + reader bake-off (~54 GB)
    python download_models.py --stage 2            # + Gemma 4 31B and gpt-oss-20b (~101 GB)
    python download_models.py --stage 3            # + Qwen3.5-122B (needs >=100 GB free)
    python download_models.py --only glm-ocr       # one model
    python download_models.py --list               # show what's on disk
    python download_models.py --delete chandra-ocr-2   # drop a bake-off loser

Each model is pinned to the commit in infra/models.yaml, so re-running this
script on a fresh scratch reproduces exactly the weights a bake-off used.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "infra" / "models.yaml"
SCRATCH_QUOTA_GB = float(os.environ.get("SCRATCH_QUOTA_GB", "200"))
STAGE3_MIN_FREE_GB = 100.0


def load_models() -> dict:
    return yaml.safe_load(REGISTRY.read_text())["models"]


def scratch_used_gb() -> float:
    """Used space under the user's scratch quota (falls back to du)."""
    user = os.environ.get("USER", "")
    try:
        out = subprocess.run(["quota", "-w", "-f", "/scratch"], capture_output=True,
                             text=True, timeout=30).stdout.splitlines()
        for line in out:
            parts = line.split()
            if parts and parts[0].startswith("/dev/") and len(parts) > 1:
                return float(parts[1].rstrip("*")) / 1024 / 1024  # KiB → GiB
    except Exception:
        pass
    out = subprocess.run(["du", "-s", "-B1G", f"/scratch/{user}"], capture_output=True, text=True)
    return float(out.stdout.split()[0]) if out.stdout else 0.0


def free_gb() -> float:
    by_quota = SCRATCH_QUOTA_GB - scratch_used_gb()
    by_fs = shutil.disk_usage(os.environ.get("HF_HOME", "/scratch")).free / 1e9
    return min(by_quota, by_fs)


def cache_dir_for(repo: str) -> Path:
    hub = Path(os.environ.get("HF_HUB_CACHE", Path(os.environ["HF_HOME"]) / "hub"))
    return hub / ("models--" + repo.replace("/", "--"))


def download(name: str, spec: dict) -> None:
    from huggingface_hub import snapshot_download

    need = float(spec.get("size_gb", 0))
    avail = free_gb()
    on_disk = cache_dir_for(spec["repo"]).exists()
    print(f"→ {name:<22} {spec['repo']}@{spec['revision'][:10]}  {need:.1f} GB  "
          f"(free {avail:.0f} GB{', partially cached' if on_disk else ''})")
    if spec.get("stage", 1) >= 3 and avail < STAGE3_MIN_FREE_GB:
        sys.exit(f"✗ refusing stage-3 model {name}: only {avail:.0f} GB free, "
                 f"need >= {STAGE3_MIN_FREE_GB:.0f} GB. Delete bake-off losers first.")
    if not on_disk and need * 1.05 > avail:
        sys.exit(f"✗ not enough space for {name}: need {need:.1f} GB, free {avail:.0f} GB")

    path = snapshot_download(
        repo_id=spec["repo"],
        revision=spec["revision"],
        allow_patterns=spec.get("allow_patterns"),
        ignore_patterns=spec.get("ignore_patterns"),
        max_workers=8,
    )
    print(f"  ✓ {path}")


def cached_repos() -> dict:
    """{repo_id: CachedRepoInfo} via huggingface_hub's scanner (blobs are shared across repos)."""
    from huggingface_hub import scan_cache_dir
    return {r.repo_id: r for r in scan_cache_dir().repos}


def list_models(models: dict) -> None:
    """Print each registry model's on-disk size and whether its pinned revision is present."""
    cached = cached_repos()
    for name, spec in models.items():
        r = cached.get(spec["repo"])
        pinned = r is not None and any(rev.commit_hash == spec["revision"] for rev in r.revisions)
        size = f"{r.size_on_disk / 1e9:6.1f} GB" if r else "     —   "
        state = "pinned rev ✓" if pinned else ("other revision" if r else "not downloaded")
        print(f"  {name:<22} stage {spec.get('stage')}  {size}  {state}")
    print(f"free under scratch quota: {free_gb():.0f} GB")


def delete_models(models: dict, names: list) -> None:
    """Delete every cached revision of these models, freeing their blobs."""
    cached = cached_repos()
    hashes = [rev.commit_hash for n in names if (r := cached.get(models[n]["repo"])) for rev in r.revisions]
    if hashes:
        from huggingface_hub import scan_cache_dir
        strategy = scan_cache_dir().delete_revisions(*hashes)
        print(f"  freeing {strategy.expected_freed_size / 1e9:.1f} GB")
        strategy.execute()


def main() -> None:
    if "HF_HOME" not in os.environ:
        sys.exit("source infra/cluster/env.sh first (HF_HOME must point at /scratch)")
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, help="download every model with stage <= N")
    ap.add_argument("--only", nargs="+", help="download just these registry names")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--delete", nargs="+", help="remove these models from the cache")
    args = ap.parse_args()
    models = load_models()

    if args.list:
        return list_models(models)
    if args.delete:
        delete_models(models, args.delete)
        return list_models(models)

    if args.only:
        todo = {n: models[n] for n in args.only}
    elif args.stage:
        todo = {n: s for n, s in models.items() if s.get("stage", 1) <= args.stage}
    else:
        ap.error("give --stage N, --only NAME..., --list or --delete NAME...")

    # Small models first so the OCR bake-off can start before the big ones land
    for name, spec in sorted(todo.items(), key=lambda kv: kv[1].get("size_gb", 0)):
        download(name, spec)
    list_models(models)


if __name__ == "__main__":
    main()
