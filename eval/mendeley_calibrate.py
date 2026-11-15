#!/usr/bin/env python3
"""mendeley_calibrate.py — can a few teacher-marked sheets teach us this teacher's strictness?

No teacher rubric is needed: the teacher marks K sheets, we learn how the grader's marks map to
this teacher's marks, and test on the other sheets. Repeated over random choices of the K sheets.

    python eval/mendeley_calibrate.py [--k 5] [--splits 20] [--grades sweep|pagetext|seg2]
    python eval/mendeley_calibrate.py fewshot [--k 5] [--seeds 0,1]   # grader sees the teacher's marked answers
    → eval/reports/mendeley_calibrate/README_*.md

Methods (all post-hoc, CPU only, on the grader's marks):
  none          grader marks as they are
  global        + mean(teacher − grader) on the K sheets
  per-question  + per-question mean(teacher − grader), shrunk towards the global shift (few examples)
  mapping       grader mark m → mean teacher mark given m on the K sheets (falls back to global)
Every result is clipped to [0, 2] and rounded to the nearest 0.5 like a real mark.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

import dataset  # noqa: E402
from mendeley_sweep import subj_metrics  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
OUT = ROOT / "eval" / "reports" / "mendeley_calibrate"


def records(source: str):
    """[(sheet, qid, grader mark, teacher mark)] — not-located answers are left out (they go to a TA)."""
    sheets = list(dataset.load(str(SET)))
    if source == "sweep":
        g = json.loads((ROOT / "eval/reports/mendeley_sweep/grades.json").read_text())
        get = lambda s, q: (g.get(f"{s}|{q}|gemma-v2|qwen+glm") or {}).get("marks")   # noqa: E731
        located = lambda s, q: bool(json.loads((ROOT / f"eval/reports/mendeley/{s}.json").read_text())  # noqa: E731
                                    ["questions"].get(q, {}).get("crop"))
    else:
        g = json.loads((ROOT / f"eval/reports/mendeley_seg/grades_{source}.json").read_text())   # per-variant cache
        get = lambda s, q: (g.get(f"{s}|{q}|{source}") or {}).get("marks")   # noqa: E731
        located = lambda s, q: get(s, q) is not None                          # noqa: E731
    out = []
    for sh in sheets:
        for i in range(1, 16):
            q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            if t is None or not 0 <= t <= 2 or not located(sh.sheet_id, q):
                continue
            m = get(sh.sheet_id, q)
            if m is not None:
                out.append((sh.sheet_id, q, float(m), float(t)))
    return out


def as_mark(x: float) -> float:
    """Clip to [0, 2] and round to the nearest half mark."""
    return min(2.0, max(0.0, round(x * 2) / 2))


def fit(train, method: str, shrink: float = 3.0):
    """Return predict(qid, grader mark) learned from the calibration answers."""
    if method == "none":
        return lambda q, m: m
    gshift = statistics.mean(t - m for _, _, m, t in train)
    if method == "global":
        return lambda q, m: as_mark(m + gshift)
    if method == "per-question":
        # shrink each question's shift towards the global one: (n·mean + k·global) / (n + k)
        per = {}
        for _, q, m, t in train:
            per.setdefault(q, []).append(t - m)
        sh = {q: (sum(v) + shrink * gshift) / (len(v) + shrink) for q, v in per.items()}
        return lambda q, m: as_mark(m + sh.get(q, gshift))
    if method == "mapping":
        by = {}
        for _, _, m, t in train:
            by.setdefault(m, []).append(t)
        mp = {m: statistics.mean(v) for m, v in by.items() if len(v) >= 3}
        return lambda q, m: as_mark(mp[m]) if m in mp else as_mark(m + gshift)
    raise ValueError(method)


# ── few-shot: the grader sees this teacher's marked answers to the same question ──

def fewshot(args):
    from concurrent.futures import ThreadPoolExecutor
    from app.pipeline.grader import grade
    from arch_sweep import endpoint
    ep = endpoint("gemma4-31b-fp8")
    sweep = json.loads((ROOT / "eval/reports/mendeley_sweep/grades.json").read_text())
    sheets = {sh.sheet_id: sh for sh in dataset.load(str(SET))}
    reads = {s: json.loads((ROOT / f"eval/reports/mendeley/{s}.json").read_text())["questions"] for s in sheets}
    tx = lambda s, q, r: ((reads[s].get(q, {}).get("readings") or {}).get(r) or {}).get("value", "")   # noqa: E731
    cache_f = OUT / "fewshot.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    md = [f"# Few-shot teacher calibration ({args.k} teacher-marked sheets, Mendeley)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/mendeley_calibrate.py fewshot`. Grader Gemma + "
          "prompt v2 (p6) with, for each question, the calibration sheets' answers (Qwen transcript) and the teacher's "
          "marks. Same baseline transcripts (Qwen + GLM-OCR crops); answers not located left out. Compared on the "
          "same held-out answers with: no calibration, and the global shift learned from the same sheets.", "",
          "| seed | calibration sheets | n | method | MAE | exact | within 0.5 | QWK | bias |",
          "|---|---|---|---|---|---|---|---|---|"]
    for seed in [int(x) for x in args.seeds.split(",")]:
        calib = sorted(random.Random(seed).sample(sorted(sheets), args.k))
        ex = {}
        for s in calib:
            for i in range(1, 16):
                q, t = f"S{i}", sheets[s].gold.get(f"S{i}", {}).get("marks")
                if t is not None and 0 <= t <= 2 and reads[s].get(q, {}).get("crop") and tx(s, q, "qwen38-27b-fp8").strip():
                    ex.setdefault(q, []).append((tx(s, q, "qwen38-27b-fp8"), t))
        jobs = []
        for s, sh in sheets.items():
            if s in calib:
                continue
            for i in range(1, 16):
                q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
                if t is None or not 0 <= t <= 2 or not reads[s].get(q, {}).get("crop"):   # CSV has a "4" for a 2-mark question
                    continue
                jobs.append((f"{s}|{q}|seed{seed}", s, q, i - 1, t))

        def run(job):
            key, s, q, qi, _t = job
            if key in cache:
                return key, cache[key]
            a, b = tx(s, q, "qwen38-27b-fp8"), tx(s, q, "glm-ocr")
            if not a.strip() and not b.strip():
                return key, {"marks": 0.0, "latency": 0.0}
            sh = sheets[s]
            g = grade(ep, sh.paper["subjectiveQuestions"][qi], sh.paper["subjectiveRubrics"][qi], a, b, [],
                      sh.paper.get("subject", ""), 2.0, version="v2", examples=ex.get(q, []))
            return key, {"marks": g.marks, "latency": g.latency_s, "error": g.error}

        with ThreadPoolExecutor(32) as pool:
            for n, (key, r) in enumerate(pool.map(run, jobs)):
                cache[key] = r
                if n % 100 == 99:
                    cache_f.write_text(json.dumps(cache))
                    print(f"seed {seed}: {n + 1}/{len(jobs)}", flush=True)
        cache_f.write_text(json.dumps(cache))
        # compare on the same answers
        base = {(s, q): sweep[f"{s}|{q}|gemma-v2|qwen+glm"]["marks"] for _, s, q, _, _ in jobs}
        train = [(s, q, float(sweep[f"{s}|{q}|gemma-v2|qwen+glm"]["marks"]), float(sheets[s].gold[q]["marks"]))
                 for s in calib for q in ex if f"{s}|{q}|gemma-v2|qwen+glm" in sweep and sheets[s].gold.get(q, {}).get("marks") is not None
                 and reads[s].get(q, {}).get("crop")]
        shift = fit(train, "global")
        rows = {"none": [(base[(s, q)], t) for _, s, q, _, t in jobs],
                "global shift": [(shift(q, base[(s, q)]), t) for _, s, q, _, t in jobs],
                "few-shot": [(cache[k]["marks"], t) for k, s, q, _, t in jobs]}
        for name, pairs in rows.items():
            m = subj_metrics(pairs)
            md.append(f"| {seed} | {', '.join(c.split('_')[1] for c in calib)} | {m['n']} | {name} | {m['mae']} | "
                      f"{m['exact']} | {m['within_0.5']} | {m['qwk']} | {m['bias']} |")
        lat = [cache[k]["latency"] for k, *_ in jobs]
        md.append(f"| {seed} | | | few-shot grader s/answer | {statistics.mean(lat):.1f} | | | | |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"README_fewshot_k{args.k}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "fewshot":
        ap = argparse.ArgumentParser()
        ap.add_argument("cmd")
        ap.add_argument("--k", type=int, default=5)
        ap.add_argument("--seeds", default="0,1")
        return fewshot(ap.parse_args())
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5, help="teacher-marked calibration sheets")
    ap.add_argument("--splits", type=int, default=20)
    ap.add_argument("--grades", default="sweep", choices=["sweep", "pagetext", "seg2"])
    args = ap.parse_args()
    recs = records(args.grades)
    sheet_ids = sorted({s for s, *_ in recs})
    methods = ["none", "global", "per-question", "mapping"]
    res = {m: [] for m in methods}
    rng = random.Random(0)
    for _ in range(args.splits):
        calib = set(rng.sample(sheet_ids, args.k))
        train = [r for r in recs if r[0] in calib]
        test = [r for r in recs if r[0] not in calib]
        for m in methods:
            f = fit(train, m)
            res[m].append(subj_metrics([(f(q, g), t) for _, q, g, t in test]))

    md = [f"# Teacher calibration from {args.k} marked sheets (Mendeley)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/mendeley_calibrate.py --k {args.k} "
          f"--grades {args.grades}`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). "
          f"{len(recs)} answers on {len(sheet_ids)} sheets; {args.splits} random choices of the {args.k} calibration "
          "sheets, tested on the remaining sheets; mean (min–max over splits).", "",
          "| method | MAE | exact | within 0.5 | QWK | bias |", "|---|---|---|---|---|---|"]
    for m in methods:
        r = res[m]
        cell = lambda k: (f"{statistics.mean(x[k] for x in r):.3f} "                       # noqa: E731
                          f"({min(x[k] for x in r):.2f}–{max(x[k] for x in r):.2f})")
        md.append(f"| {m} | {cell('mae')} | {cell('exact')} | {cell('within_0.5')} | {cell('qwk')} | {cell('bias')} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"README_{args.grades}_k{args.k}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
