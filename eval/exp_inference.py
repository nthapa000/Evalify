#!/usr/bin/env python3
"""exp_inference.py — inference-optimisation experiments: speed AND accuracy of each serving set-up.

    python eval/exp_inference.py run   --config baseline [--endpoints FILE] [--levels 16 32] [--ds-sheets 48]
    python eval/exp_inference.py score                        # writes eval/reports/exp_inference/README.md

run:   marks real labelled sheets through orchestrator.run with N sheets in flight, for each workload
       (one-page handwritten MCQ / MCQ+numerical; Data Science MCQ + 15 written answers). Records wall time,
       tokens, the vLLM servers' KV-cache use and queue (sampled from /metrics), and every sheet's result.
score: one table for speed, one for accuracy (vs the labels and vs the baseline's own marks — any
       optimisation must not change the marks more than re-running the baseline does).
Client-side switches are read from the environment and stored with each run (EVALIFY_IMAGE_MAX_PIXELS,
EVALIFY_GRADE_LAYOUT). Log of all steps: INFERENCE_OPTIMIZATION.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics as st
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "reports" / "exp_inference"
CLIENT_SWITCHES = ("EVALIFY_IMAGE_MAX_PIXELS", "EVALIFY_GRADE_LAYOUT")


# ── Accuracy helpers (pure; unit-tested) ─────────────────────────────────────

def same_mcq(read: str, gold: str) -> bool:
    """MCQ answers equal as sets of letters ("A, C" == "C,A")."""
    letters = lambda s: sorted(set(re.findall(r"[A-D]", str(s or "").upper())))
    return letters(read) == letters(gold)


def closed_accuracy(answers: dict, gold: dict) -> tuple:
    """(correct, total) for MCQ (Q*) and numerical (N*) answers with a gold answer."""
    from app.pipeline import numeric
    ok = n = 0
    for qid, g in gold.items():
        if "answer" not in g or not (qid.startswith("Q") or qid.startswith("N")):
            continue
        n += 1
        read = answers.get(qid, "")
        if qid.startswith("Q"):
            ok += same_mcq(read, g["answer"])
        else:
            ok += numeric.compare(read, g["answer"]).status == "correct"
    return ok, n


def marks_error(marks: dict, gold: dict) -> list:
    """|our mark − teacher's mark| for every written answer the teacher marked."""
    return [abs(marks.get(q, 0.0) - g["marks"]) for q, g in gold.items()
            if q.startswith("S") and g.get("marks") is not None]


def agreement(a: dict, b: dict) -> tuple:
    """(same, total) over keys present in both — how often two runs gave the same answer / mark."""
    keys = [k for k in a if k in b]
    return sum(a[k] == b[k] for k in keys), len(keys)


def parse_metrics(text: str) -> dict:
    """KV-cache use (0–1) and waiting requests from a vLLM /metrics page."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"vllm:(kv_cache_usage_perc|gpu_cache_usage_perc|num_requests_waiting|num_requests_running)"
                     r"\{[^}]*\}\s+([0-9.eE+-]+)", line)
        if m:
            key = {"gpu_cache_usage_perc": "kv", "kv_cache_usage_perc": "kv"}.get(m.group(1), m.group(1))
            out[key] = max(out.get(key, 0.0), float(m.group(2)))
    return out


# ── Running ──────────────────────────────────────────────────────────────────

class Sampler(threading.Thread):
    """Polls every server's /metrics while a batch runs; keeps the peaks and the average KV use."""

    def __init__(self, urls: dict):
        super().__init__(daemon=True)
        self.urls, self.stop, self.samples = urls, threading.Event(), {n: [] for n in urls}

    def run(self):
        import requests
        while not self.stop.is_set():
            for name, url in self.urls.items():
                try:
                    self.samples[name].append(parse_metrics(requests.get(url, timeout=2).text))
                except Exception:
                    pass
            self.stop.wait(2)

    def summary(self) -> dict:
        res = {}
        for name, ss in self.samples.items():
            if ss:
                kv = [s.get("kv", 0) for s in ss]
                res[name] = {"kv_peak": round(max(kv), 3), "kv_mean": round(st.mean(kv), 3),
                             "waiting_peak": int(max(s.get("num_requests_waiting", 0) for s in ss)),
                             "running_peak": int(max(s.get("num_requests_running", 0) for s in ss))}
        return res


def one_sheet(sheet) -> dict:
    """Evaluate one sheet on a copy of its pages; keep what is needed for accuracy and agreement."""
    from app.pipeline import orchestrator
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        for i, p in enumerate(sheet.pages):
            dst = Path(tmp) / f"p{i}{Path(p).suffix}"
            shutil.copy(p, dst)
            pages.append(str(dst))
        t0 = time.time()
        out = orchestrator.run(sheet.paper, pages, sheet.sheet_type)
    return {"sheet": sheet.sheet_id, "latency_s": round(time.time() - t0, 1), "usage": out["usage"],
            "answers": out["answers"], "review": sorted(r["question"] for r in out["review"]),
            "marks": {d["question"]: d["marks_earned"] for d in out["subjective_detail"]},
            "gold": sheet.gold}


def workloads(ds_sheets: int) -> dict:
    """The same real sheets as exp_tokens / exp_throughput."""
    import dataset
    closed = [s for f in ("own_mcq", "own_mcqnum") for s in dataset.load(str(DATA / f))]
    ds = list(dataset.load(str(DATA / "mendeley")))[:ds_sheets]
    return {"one-page": closed, "data-science": ds}


def run(args) -> None:
    os.environ["EVALIFY_ENDPOINTS_FILE"] = args.endpoints          # before the pipeline is imported
    sys.path.insert(0, str(HERE.parents[0] / "backend"))
    sys.path.insert(0, str(HERE))
    from app.pipeline import llm
    eps = json.loads(Path(args.endpoints).read_text())
    metrics = {n: m["base_url"].rsplit("/v1", 1)[0] + "/metrics" for n, m in eps["models"].items()}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "runs").mkdir(exist_ok=True)
    switches = {k: os.environ.get(k, "") for k in CLIENT_SWITCHES}
    for wname, sheets in workloads(args.ds_sheets).items():
        if args.workloads and wname not in args.workloads:
            continue
        for level in args.levels:
            sampler = Sampler(metrics)
            sampler.start()
            t0 = time.time()
            with ThreadPoolExecutor(level) as pool:
                rows = list(pool.map(llm.carry(one_sheet), sheets))
            wall = time.time() - t0
            sampler.stop.set()
            tok = sum(r["usage"]["total_tokens"] for r in rows)
            res = {"config": args.config, "workload": wname, "concurrency": level, "sheets": len(rows),
                   "wall_s": round(wall, 1), "sheets_per_hour": round(len(rows) / wall * 3600, 1),
                   "mean_sheet_latency_s": round(st.mean(r["latency_s"] for r in rows), 1),
                   "tokens": tok, "tokens_per_s": round(tok / wall), "profile": eps.get("profile"),
                   "job": eps.get("job_id"), "switches": switches, "servers": sampler.summary(),
                   "errors": sum(1 for r in rows if r["usage"]["calls"] == 0), "time": time.strftime("%F %T")}
            name = f"{args.config}__{wname}__c{level}.json"
            (OUT / "runs" / name).write_text(json.dumps({"summary": res, "sheets": rows}, indent=1))
            print(json.dumps(res), flush=True)


# ── Scoring ──────────────────────────────────────────────────────────────────

def _acc(rows: list) -> dict:
    """Accuracy of one run against the labels."""
    ok = n = 0
    err, ta = [], 0
    for r in rows:
        a, b = closed_accuracy(r["answers"], r["gold"])
        ok, n = ok + a, n + b
        err += marks_error(r["marks"], r["gold"])
        ta += len(r["review"])
    return {"closed": f"{ok}/{n} ({ok / n:.1%})" if n else "-",
            "mae": f"{st.mean(err):.3f}" if err else "-", "ta": ta}


def _agree(rows: list, ref: list) -> str:
    """Same answers / marks as the reference run, per question."""
    ref_by = {r["sheet"]: r for r in ref}
    s = n = 0
    for r in rows:
        if r["sheet"] in ref_by:
            for key in ("answers", "marks"):
                a, b = agreement(r[key], ref_by[r["sheet"]][key])
                s, n = s + a, n + b
    return f"{s}/{n} ({s / n:.1%})" if n else "-"


def score(_args) -> None:
    sys.path.insert(0, str(HERE.parents[0] / "backend"))
    runs = [json.loads(p.read_text()) for p in sorted((OUT / "runs").glob("*.json"))]
    runs.sort(key=lambda r: r["summary"]["time"])
    base = {(r["summary"]["workload"], r["summary"]["concurrency"]): r["sheets"]
            for r in runs if r["summary"]["config"] == "baseline"}
    md = ["# Inference optimisation: speed and accuracy per set-up", "",
          "`python eval/exp_inference.py score`. Each row = one batch of real sheets marked with N sheets in flight.",
          "*KV peak / queue peak*: highest KV-cache use and most requests waiting on the Gemma (A6000 or",
          "wherever it runs) and Qwen servers during the batch. Steps and decisions: `INFERENCE_OPTIMIZATION.md`.", "",
          "## Speed", "",
          "| Set-up | Workload | In flight | Sheets | Wall | **Sheets / h** | Tokens / s | Gemma KV peak / queue "
          "| Qwen KV peak / queue | Errors |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        s = r["summary"]
        g, q = s["servers"].get("gemma4-31b-fp8", {}), s["servers"].get("qwen38-27b-fp8", {})
        kvq = lambda d: f"{d['kv_peak']:.0%} / {d['waiting_peak']}" if d else "-"
        md.append(f"| {s['config']} | {s['workload']} | {s['concurrency']} | {s['sheets']} | {s['wall_s']:.0f} s "
                  f"| **{s['sheets_per_hour']:.0f}** | {s['tokens_per_s']:,} | {kvq(g)} | {kvq(q)} | {s['errors']} |")
    md += ["", "## Accuracy", "",
           "*MCQ / numerical*: answers read correctly vs the labels. *Written MAE*: mean |our mark − teacher|",
           "(0–2 per answer). *Same as baseline*: answers and marks identical to the baseline run with the same",
           "workload and concurrency (the baseline against itself at another concurrency is the noise floor).", "",
           "| Set-up | Workload | In flight | MCQ / numerical correct | Written MAE | TA items | Same as baseline |",
           "|---|---|---|---|---|---|---|"]
    for r in runs:
        s = r["summary"]
        a = _acc(r["sheets"])
        ref = base.get((s["workload"], s["concurrency"]))
        if s["config"] == "baseline":
            other = [v for (w, c), v in base.items() if w == s["workload"] and c != s["concurrency"]]
            same = f"noise floor: {_agree(r['sheets'], other[0])}" if other else "-"
        else:
            same = _agree(r["sheets"], ref) if ref else "-"
        md.append(f"| {s['config']} | {s['workload']} | {s['concurrency']} | {a['closed']} | {a['mae']} "
                  f"| {a['ta']} | {same} |")
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print((OUT / "README.md").read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True)
    r.add_argument("--endpoints", default="/scratch/m25csa019/evalify/run/endpoints.json")
    r.add_argument("--levels", type=int, nargs="+", default=[16, 32])
    r.add_argument("--ds-sheets", type=int, default=48)
    r.add_argument("--workloads", nargs="*", default=[])
    sub.add_parser("score")
    a = ap.parse_args()
    {"run": run, "score": score}[a.cmd](a)
