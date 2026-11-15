#!/usr/bin/env python3
"""exp_consistency.py — how consistent is the grader with itself? (experiment only; pipeline unchanged)

    python eval/exp_consistency.py run      # GPU: re-grade every pagetext answer (a) same input, (b) A/B swapped
    python eval/exp_consistency.py score    # → eval/reports/exp_consistency/README.md

Grader = Gemma + prompt v2 (final set-up), transcripts = pagetext (Qwen + Gemma whole page). Compares:
  (a) same input graded twice (temperature 0, so this is a sanity check)
  (b) same answer, the two transcripts swapped (A↔B) — presentation should not change the mark
  (c) same answer, transcripts from two segmentation methods (pagetext vs seg2) — reading noise
  (d) two different graders on the same transcripts (Gemma v2 vs Qwen v2, first run) — "two TAs"
  (e) the teacher vs our grader (for scale)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

import dataset  # noqa: E402
from mendeley_sweep import subj_metrics  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
SEG = ROOT / "eval" / "reports" / "mendeley_seg"
OUT = ROOT / "eval" / "reports" / "exp_consistency"


def cmd_run(_args):
    from app.pipeline.grader import grade
    from arch_sweep import endpoint
    ep = endpoint("gemma4-31b-fp8")
    reads = json.loads((SEG / "read_pagetext.json").read_text())
    sheets = {sh.sheet_id: sh for sh in dataset.load(str(SET))}
    f = OUT / "grades.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    jobs = []
    for s, sh in sheets.items():
        for i in range(1, 16):
            q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            a = reads.get(s, {}).get("answers", {}).get(q)
            if t is None or not 0 <= t <= 2 or not a or not (a["a"].strip() or a["b"].strip()):
                continue
            for mode in ("repeat", "swap"):
                if f"{s}|{q}|{mode}" not in cache:
                    jobs.append((f"{s}|{q}|{mode}", s, q, i - 1, a, mode))

    def run(job):
        key, s, q, qi, a, mode = job
        ta, tb = (a["a"], a["b"]) if mode == "repeat" else (a["b"], a["a"])   # swap = B shown first
        sh = sheets[s]
        g = grade(ep, sh.paper["subjectiveQuestions"][qi], sh.paper["subjectiveRubrics"][qi], ta, tb, [],
                  sh.paper.get("subject", ""), 2.0, version="v2")
        return key, {"marks": g.marks, "latency": g.latency_s, "error": g.error}

    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(32) as pool:
        for n, (key, r) in enumerate(pool.map(run, jobs)):
            cache[key] = r
            if n % 100 == 99:
                f.write_text(json.dumps(cache))
                print(f"{n + 1}/{len(jobs)}", flush=True)
    f.write_text(json.dumps(cache))
    print(f"done: {len(jobs)} gradings")


def agree(pairs):
    """Agreement between two lists of marks: exact, within 0.5, differ by ≥ 1 mark, MAE, QWK."""
    m = subj_metrics(pairs)
    big = sum(abs(a - b) >= 1 for a, b in pairs) / len(pairs)
    return f"{m['n']} | {m['exact']:.0%} | {m['within_0.5']:.0%} | {big:.0%} | {m['mae']} | {m['qwk']}"


def cmd_score(_args):
    sheets = {sh.sheet_id: sh for sh in dataset.load(str(SET))}
    pt = json.loads((SEG / "grades_pagetext.json").read_text())
    s2 = json.loads((SEG / "grades_seg2.json").read_text())
    sw = json.loads((ROOT / "eval/reports/mendeley_sweep/grades.json").read_text())
    ex = json.loads((OUT / "grades.json").read_text()) if (OUT / "grades.json").exists() else {}
    rows = {"a": [], "b": [], "c": [], "d": [], "e": []}
    for s, sh in sheets.items():
        for i in range(1, 16):
            q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            if t is None or not 0 <= t <= 2:
                continue
            base = (pt.get(f"{s}|{q}|pagetext") or {}).get("marks")
            if base is None:
                continue
            for k, mode in (("a", "repeat"), ("b", "swap")):
                if f"{s}|{q}|{mode}" in ex and not ex[f"{s}|{q}|{mode}"].get("error"):
                    rows[k].append((base, ex[f"{s}|{q}|{mode}"]["marks"]))
            other = (s2.get(f"{s}|{q}|seg2") or {}).get("marks")
            if other is not None:
                rows["c"].append((base, other))
            g, qw = sw.get(f"{s}|{q}|gemma-v2|qwen+glm"), sw.get(f"{s}|{q}|qwen-v2|qwen+glm")
            if g and qw and not g.get("blank"):
                rows["d"].append((g["marks"], qw["marks"]))
            rows["e"].append((base, float(t)))
    names = {"a": "(a) same input graded twice", "b": "(b) transcripts A↔B swapped",
             "c": "(c) two reading methods (pagetext vs seg2)", "d": "(d) two graders, same transcripts (Gemma vs Qwen)",
             "e": "(e) our grader vs the teacher"}
    md = ["# Grader consistency (Mendeley, experiment)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/exp_consistency.py score`. Grader Gemma + "
          "prompt v2, temperature 0; marks 0–2 in steps of 0.5. *≥1 apart* = the two marks differ by a mark or more.",
          "", "| comparison | n | exact | within 0.5 | ≥ 1 apart | MAE | QWK |", "|---|---|---|---|---|---|---|"]
    for k, v in rows.items():
        if v:
            md.append(f"| {names[k]} | {agree(v)} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    a = ap.parse_args()
    {"run": cmd_run, "score": cmd_score}[a.cmd](a)
