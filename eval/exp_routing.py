#!/usr/bin/env python3
"""exp_routing.py — which TA-flagging rules for written answers catch the most wrong marks per TA item?

    python eval/exp_routing.py run     # GPU: grade the 555 Mendeley answers like production, keep full grader output
    python eval/exp_routing.py score   # → eval/reports/exp_routing/README.md

Production set-up: whole-page transcripts (pagetext, Qwen + Gemma), grader Gemma + prompt v2, transcripts only.
"Wrong" = grader mark ≥ 1 away from the teacher's mark (out of 2), measured both raw and after the per-question
calibration shift (learned on 10 sheets; tested on the other 40) so that the teacher's general leniency — which no
routing rule can see — is taken out.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

import dataset  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
SEG = ROOT / "eval" / "reports" / "mendeley_seg"
OUT = ROOT / "eval" / "reports" / "exp_routing"


def items():
    """(sheet, qid, qi, teacher mark, transcripts A/B) for every located, teacher-marked answer."""
    sheets = {sh.sheet_id: sh for sh in dataset.load(str(SET))}
    reads = json.loads((SEG / "read_pagetext.json").read_text())
    out = []
    for s, sh in sheets.items():
        for i in range(1, 16):
            q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            a = reads.get(s, {}).get("answers", {}).get(q)
            if t is not None and 0 <= t <= 2 and a and (a["a"].strip() or a["b"].strip()):
                out.append((s, q, i - 1, float(t), a))
    return sheets, out


def cmd_run(_args):
    from app.pipeline.grader import grade
    from arch_sweep import endpoint
    ep = endpoint("gemma4-31b-fp8")
    sheets, its = items()
    f = OUT / "grades.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    todo = [x for x in its if f"{x[0]}|{x[1]}" not in cache]

    def run(x):
        s, q, qi, _t, a = x
        sh = sheets[s]
        g = grade(ep, sh.paper["subjectiveQuestions"][qi], sh.paper["subjectiveRubrics"][qi], a["a"], a["b"], [],
                  sh.paper.get("subject", ""), 2.0, version="v2")
        return f"{s}|{q}", {"marks": g.marks, "error": g.error, "transcript_problem": g.transcript_problem,
                            "concepts": [{"present": d.present, "partial": d.partial, "confidence": d.confidence,
                                          "evidence_found": d.evidence_found} for d in g.decisions]}

    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(32) as pool:
        for n, (k, r) in enumerate(pool.map(run, todo)):
            cache[k] = r
            if n % 100 == 99:
                f.write_text(json.dumps(cache))
                print(f"{n + 1}/{len(todo)}", flush=True)
    f.write_text(json.dumps(cache))
    print(f"done: {len(todo)} gradings")


def flags(rec, a, b, rule):
    """Would this rule send the answer to a TA?"""
    from app.pipeline.readers import text_similarity
    conf = [c["confidence"] for c in rec["concepts"] if c["confidence"] is not None]
    reasons = {
        "low_conf": bool(conf) and min(conf) < rule["conf"],
        "evidence": rule["evidence"] and any(not c["evidence_found"] for c in rec["concepts"]),
        "transcript_problem": rule["tp"] and rec["transcript_problem"],
        "transcripts_differ": rule["sim"] > 0 and bool(a.strip()) and bool(b.strip()) and text_similarity(a, b) < rule["sim"],
        "error": bool(rec["error"]),
    }
    return any(reasons.values())


def cmd_score(_args):
    from app.pipeline import calibration as cal
    sheets, its = items()
    grades = json.loads((OUT / "grades.json").read_text())
    its = [x for x in its if f"{x[0]}|{x[1]}" in grades]
    # Per-question calibration learned on 10 random sheets, evaluated on the others
    calib = set(random.Random(0).sample(sorted({x[0] for x in its}), 10))
    fitted = cal.fit([(q, grades[f"{s}|{q}"]["marks"], t) for s, q, _, t, _ in its if s in calib])
    test = [x for x in its if x[0] not in calib]
    rules = [{"name": "nothing (all auto)", "conf": 0, "evidence": False, "tp": False, "sim": 0}]
    for c in (0.5, 0.6, 0.7, 0.8, 0.9):
        rules.append({"name": f"confidence < {c}", "conf": c, "evidence": False, "tp": False, "sim": 0})
    rules += [{"name": "evidence not found", "conf": 0, "evidence": True, "tp": False, "sim": 0},
              {"name": "transcript problem", "conf": 0, "evidence": False, "tp": True, "sim": 0},
              {"name": "transcripts differ (< 0.6)", "conf": 0, "evidence": False, "tp": False, "sim": 0.6},
              {"name": "current defaults (conf < 0.7 + evidence + transcript problem)", "conf": 0.7, "evidence": True, "tp": True, "sim": 0}]
    for c in (0.6, 0.8):
        rules.append({"name": f"conf < {c} + evidence + transcript problem", "conf": c, "evidence": True, "tp": True, "sim": 0})
    md = ["# TA-flagging rules for written answers (Mendeley, experiment)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/exp_routing.py score`. {len(test)} answers on the "
          f"40 sheets not used for calibration. *Wrong* = ≥ 1 mark away from the teacher (out of 2). *Calibrated* = after "
          "the per-question shift learned on 10 sheets. A good rule sends few answers to a TA and catches many wrong ones.",
          "", "| rule | to TA | wrong caught (raw) | wrong left auto (raw) | wrong caught (calibrated) | wrong left auto (calibrated) | wrong rate in TA vs auto (cal.) |",
          "|---|---|---|---|---|---|---|"]
    for rule in rules:
        ta = auto = cr = ar = cc = ac = 0
        for s, q, _, t, a in test:
            g = grades[f"{s}|{q}"]
            calm = cal.apply(fitted, q, g["marks"], 2.0)
            wr, wc = abs(g["marks"] - t) >= 1, abs(calm - t) >= 1
            if flags(g, a["a"], a["b"], rule):
                ta += 1; cr += wr; cc += wc
            else:
                auto += 1; ar += wr; ac += wc
        rate = f"{cc / ta:.0%} vs {ac / auto:.0%}" if ta and auto else "—"
        md.append(f"| {rule['name']} | {ta} ({ta / len(test):.0%}) | {cr} | {ar} | {cc} | {ac} | {rate} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    a = ap.parse_args()
    {"run": cmd_run, "score": cmd_score}[a.cmd](a)
