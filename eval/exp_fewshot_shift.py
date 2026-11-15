#!/usr/bin/env python3
"""exp_fewshot_shift.py — few-shot examples + shift, with K teacher-marked sheets (experiment only).

    python eval/exp_fewshot_shift.py run   [--k 10] [--seeds 0,1]   # GPU
    python eval/exp_fewshot_shift.py score [--k 10] [--seeds 0,1]   # → eval/reports/exp_fewshot_shift/README.md

Transcripts = pagetext (final set-up); grader = Gemma + prompt v2 with the teacher's marked answers to the same
question as examples (prompt p6). To learn a shift *on few-shot marks* fairly, every calibration sheet is graded
with examples from the OTHER calibration sheets only (leave-one-sheet-out); held-out sheets see all K sheets.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

import dataset  # noqa: E402
from mendeley_sweep import subj_metrics  # noqa: E402
from mendeley_calibrate import fit  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
SEG = ROOT / "eval" / "reports" / "mendeley_seg"
OUT = ROOT / "eval" / "reports" / "exp_fewshot_shift"


def load_all():
    sheets = {sh.sheet_id: sh for sh in dataset.load(str(SET))}
    reads = json.loads((SEG / "read_pagetext.json").read_text())
    base = json.loads((SEG / "grades_pagetext.json").read_text())
    items = []                                       # (sheet, qid, qi, teacher, transcripts) for located answers
    for s, sh in sheets.items():
        for i in range(1, 16):
            q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            a = reads.get(s, {}).get("answers", {}).get(q)
            if t is None or not 0 <= t <= 2 or not a or (base.get(f"{s}|{q}|pagetext") or {}).get("marks") is None:
                continue
            items.append((s, q, i - 1, float(t), a))
    return sheets, base, items


def split(sheets, k, seed):
    return set(random.Random(seed).sample(sorted(sheets), k))


def examples_for(items, q, from_sheets):
    """Teacher-marked answers to question q from the given sheets (Qwen whole-page transcript)."""
    return [(a["a"] or a["b"], t) for s, qq, _, t, a in items if qq == q and s in from_sheets and (a["a"] or a["b"]).strip()]


def cmd_run(args):
    from app.pipeline.grader import grade
    from arch_sweep import endpoint
    ep = endpoint("gemma4-31b-fp8")
    sheets, _, items = load_all()
    f = OUT / "grades.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    OUT.mkdir(parents=True, exist_ok=True)
    for seed in [int(x) for x in args.seeds.split(",")]:
        calib = split(sheets, args.k, seed)
        jobs = [(f"k{args.k}|seed{seed}|{s}|{q}", s, q, qi, a, calib - {s} if s in calib else calib)
                for s, q, qi, _, a in items if f"k{args.k}|seed{seed}|{s}|{q}" not in cache]

        def run(job):
            key, s, q, qi, a, ex_from = job
            sh = sheets[s]
            g = grade(ep, sh.paper["subjectiveQuestions"][qi], sh.paper["subjectiveRubrics"][qi], a["a"], a["b"], [],
                      sh.paper.get("subject", ""), 2.0, version="v2", examples=examples_for(items, q, ex_from))
            return key, {"marks": g.marks, "latency": g.latency_s, "error": g.error}

        with ThreadPoolExecutor(32) as pool:
            for n, (key, r) in enumerate(pool.map(run, jobs)):
                cache[key] = r
                if n % 100 == 99:
                    f.write_text(json.dumps(cache))
                    print(f"seed {seed}: {n + 1}/{len(jobs)}", flush=True)
        f.write_text(json.dumps(cache))


def cmd_score(args):
    sheets, base, items = load_all()
    cache = json.loads((OUT / "grades.json").read_text())
    md = [f"# Few-shot + shift with {args.k} teacher-marked sheets (Mendeley, experiment)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/exp_fewshot_shift.py score`. Transcripts: "
          "whole page (pagetext). Grader Gemma + prompt v2. Tested on the sheets NOT used for calibration; shifts are "
          "learned on the calibration sheets only (few-shot marks there use leave-one-sheet-out examples).", "",
          "| seed | n | method | MAE | exact | within 0.5 | QWK | bias | grader s/answer |",
          "|---|---|---|---|---|---|---|---|---|"]
    for seed in [int(x) for x in args.seeds.split(",")]:
        calib = split(sheets, args.k, seed)
        key = lambda s, q: f"k{args.k}|seed{seed}|{s}|{q}"   # noqa: E731
        if any(key(s, q) not in cache for s, q, *_ in items):
            md.append(f"| {seed} | | (incomplete) | | | | | | |")
            continue
        b = lambda s, q: float(base[f"{s}|{q}|pagetext"]["marks"])   # noqa: E731
        fs = lambda s, q: float(cache[key(s, q)]["marks"])           # noqa: E731
        train_b = [(s, q, b(s, q), t) for s, q, _, t, _ in items if s in calib]
        train_f = [(s, q, fs(s, q), t) for s, q, _, t, _ in items if s in calib]
        test = [(s, q, t) for s, q, _, t, _ in items if s not in calib]
        methods = {
            "no calibration": lambda s, q: b(s, q),
            "global shift": (lambda f_: lambda s, q: f_(q, b(s, q)))(fit(train_b, "global")),
            "per-question shift": (lambda f_: lambda s, q: f_(q, b(s, q)))(fit(train_b, "per-question")),
            "few-shot": fs,
            "few-shot + global shift": (lambda f_: lambda s, q: f_(q, fs(s, q)))(fit(train_f, "global")),
            "few-shot + per-question shift": (lambda f_: lambda s, q: f_(q, fs(s, q)))(fit(train_f, "per-question")),
        }
        lat_fs = statistics.mean(cache[key(s, q)]["latency"] for s, q, _ in test)
        lat_b = statistics.mean(base[f"{s}|{q}|pagetext"].get("latency", 0) for s, q, _ in test)
        for name, f in methods.items():
            m = subj_metrics([(f(s, q), t) for s, q, t in test])
            lat = lat_fs if name.startswith("few-shot") else lat_b
            md.append(f"| {seed} | {m['n']} | {name} | {m['mae']} | {m['exact']:.0%} | {m['within_0.5']:.0%} | "
                      f"{m['qwk']} | {m['bias']} | {lat:.1f} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"README_k{args.k}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--seeds", default="0,1")
    a = ap.parse_args()
    {"run": cmd_run, "score": cmd_score}[a.cmd](a)
