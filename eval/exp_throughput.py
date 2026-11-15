#!/usr/bin/env python3
"""exp_throughput.py — how many answer sheets per hour our own GPUs can mark (self-hosting cost side).

    python eval/exp_throughput.py run [--levels 4 8 16]
    python eval/exp_throughput.py score

run:   for each concurrency level, marks a fixed batch of real sheets with N sheets in flight at once and
       records the wall-clock time; sheets/hour = batch / wall time. Two workloads: handwritten MCQ /
       MCQ+numerical sheets (1 page) and Data Science sheets (MCQ + 15 written answers, 4-6 pages).
score: writes eval/reports/exp_throughput/README.md.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402
from exp_tokens import one_sheet  # noqa: E402  (runs orchestrator.run on a copy of the pages)

DATA = Path(__file__).resolve().parent / "data"
OUT = Path(__file__).resolve().parent / "reports" / "exp_throughput"


def workloads() -> dict:
    """{name: [(label, sheet)]} — the same real sheets as the token measurement."""
    closed = [("closed", s) for f in ("own_mcq", "own_mcqnum") for s in dataset.load(str(DATA / f))]
    ds = [("ds", s) for s in dataset.load(str(DATA / "mendeley"))]
    return {"Handwritten MCQ / MCQ+numerical (1 page)": closed[:30],
            "Data Science exam (20 MCQ + 15 written, 4-6 pages)": ds[:24]}


def run(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out_file = OUT / "runs.json"
    results = json.loads(out_file.read_text()) if out_file.exists() else []
    for name, jobs in workloads().items():
        for level in args.levels:
            t0 = time.time()
            with ThreadPoolExecutor(level) as pool:
                rows = list(pool.map(lambda j: one_sheet(*j), jobs))
            wall = time.time() - t0
            tok = sum(r["usage"]["total_tokens"] for r in rows)
            out = sum(r["usage"]["completion_tokens"] for r in rows)
            res = {"workload": name, "concurrency": level, "sheets": len(rows), "wall_s": round(wall, 1),
                   "sheets_per_hour": round(len(rows) / wall * 3600, 1),
                   "mean_sheet_latency_s": round(sum(r["latency_s"] for r in rows) / len(rows), 1),
                   "tokens": tok, "tokens_per_s": round(tok / wall), "output_tokens_per_s": round(out / wall),
                   "errors": sum(1 for r in rows if r["usage"]["calls"] == 0)}
            results.append(res)
            out_file.write_text(json.dumps(results, indent=1))
            print(json.dumps(res), flush=True)
    print("saved", out_file)


def score(_args) -> None:
    rows = json.loads((OUT / "runs.json").read_text())
    md = ["# Throughput of our own GPUs", "",
          "Hardware: one node, 2 GPUs (RTX A6000 48 GB: Gemma 4 31B FP8; RTX PRO 6000 96 GB: Qwen 3.8 27B FP8 +",
          "GLM-OCR + two OCR models not used by the pipeline), vLLM. Same real sheets as `exp_tokens`.",
          "*Concurrency* = answer sheets being marked at the same time.", "",
          "| Workload | Concurrency | Sheets | Wall time | **Sheets / hour** | Time per sheet | Tokens / s |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['workload']} | {r['concurrency']} | {r['sheets']} | {r['wall_s']:.0f} s "
                  f"| **{r['sheets_per_hour']:.0f}** | {r['mean_sheet_latency_s']:.0f} s | {r['tokens_per_s']:,} |")
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print((OUT / "README.md").read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--levels", type=int, nargs="+", default=[4, 8, 16])
    sub.add_parser("score")
    a = ap.parse_args()
    {"run": run, "score": score}[a.cmd](a)
