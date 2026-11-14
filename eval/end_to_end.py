#!/usr/bin/env python3
"""end_to_end.py — Phase 0/4: run the whole grader on labelled sheets and measure the system.

    python eval/end_to_end.py eval/data/<set> --split dev                # two-reader pipeline
    python eval/end_to_end.py eval/data/<set> --split dev --legacy       # llama3.2-vision baseline

Per question: is the final mark right (vs gold), and was it routed to a TA?
Reports plan §10 system metrics overall and per paper type: coverage, accuracy on
auto-accepted items, silent error rate, TA routing rate; plus subjective QWK/MAE.
Saves per-question rows to eval/runs/e2e_<mode>_<time>.jsonl for calibrate.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402
import metrics  # noqa: E402
from reader_bakeoff import RUNS, _log_mlflow  # noqa: E402


def run_pipeline(sheet) -> dict:
    """Two-reader pipeline on one sheet → {question: (marks, max, routed, reasons, detail)}."""
    from app.pipeline import orchestrator
    out = orchestrator.run(sheet.paper, sheet.pages, sheet.sheet_type)
    rows = {}
    for d in out["mcq_detail"] + out["numerical_detail"] + out["subjective_detail"]:
        rows[d["question"]] = (d["marks_earned"], d["marks_available"], d["needs_review"], d["review_reasons"], d)
    return rows


def run_legacy(sheet) -> dict:
    """Legacy single-model Ollama path (Phase 0 baseline); it never routes anything."""
    from app.pipeline.scoring import grade_mcq, grade_numerical
    from app.services import evaluator
    qs = sheet.paper
    n_mcq = int(qs.get("mcqCount", 0))
    n_num = int(qs.get("numericalCount", 0)) if "numerical" in qs.get("type", "") else 0
    n_subj = int(qs.get("subjectiveCount", 0)) if "subjective" in qs.get("type", "") else 0
    answers, *_ = evaluator._extract_all(sheet.pages, sheet.sheet_type, n_mcq, n_num, n_subj)
    detail = grade_mcq(answers, qs, n_mcq)[2] + grade_numerical(answers, qs, n_num)[1] \
        + evaluator._grade_subjective(answers, qs, n_subj)[1]
    return {d["question"]: (d["marks_earned"], d["marks_available"], False, [], d) for d in detail}


def gold_marks(sheet, qid: str, max_marks: float):
    """Gold marks: explicit 'marks', else full/zero from the gold answer via deterministic scoring."""
    g = sheet.gold.get(qid, {})
    if "marks" in g:
        return float(g["marks"])
    if "answer" in g:
        from app.pipeline.scoring import grade_mcq, grade_numerical
        if qid.startswith("Q"):
            n = int(sheet.paper.get("mcqCount", 0))
            return next(d["marks_earned"] for d in grade_mcq({qid: g["answer"]}, sheet.paper, n)[2] if d["question"] == qid)
        n = int(sheet.paper.get("numericalCount", 0))
        return next(d["marks_earned"] for d in grade_numerical({qid: g["answer"]}, sheet.paper, n)[1] if d["question"] == qid)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--legacy", action="store_true", help="run the old Ollama path instead")
    args = ap.parse_args()
    mode = "legacy" if args.legacy else "pipeline"
    if args.legacy:
        os.environ["EVALIFY_PIPELINE"] = "legacy"

    # Grade every sheet; compare each question's final mark with gold
    rows, t0 = [], time.time()
    for sh in dataset.load(args.set_dir, args.split):
        res = (run_legacy if args.legacy else run_pipeline)(sh)
        for qid, (marks, mx, routed, reasons, detail) in res.items():
            gm = gold_marks(sh, qid, mx)
            if gm is None:
                continue
            rows.append({"sheet": sh.sheet_id, "q": qid, "paper_type": sh.paper.get("type"),
                         "kind": {"Q": "mcq", "N": "numerical", "S": "subjective"}[qid[0]],
                         "marks": marks, "gold": gm, "max": mx, "correct": abs(marks - gm) < 1e-6,
                         "routed": routed, "reasons": reasons,
                         "readings": detail.get("readings"), "concepts": detail.get("concepts"),
                         "second_grader_marks": detail.get("second_grader_marks")})
        print(f"  {sh.sheet_id}: {sum(r['routed'] for r in rows if r['sheet'] == sh.sheet_id)} routed")

    # System metrics overall, per paper type, per question kind
    report = {"all": metrics.system_metrics(rows)}
    for key in ("paper_type", "kind"):
        groups = defaultdict(list)
        for r in rows:
            groups[r[key]].append(r)
        report.update({f"{key}={k}": metrics.system_metrics(v) for k, v in groups.items()})
    subj = [r for r in rows if r["kind"] == "subjective"]
    if subj:
        g, p = [r["gold"] for r in subj], [r["marks"] for r in subj]
        report["subjective_marks"] = {"qwk": metrics.qwk(g, p), "mae": metrics.mae(g, p),
                                      "exact": metrics.agreement(g, p), "within_1": metrics.agreement(g, p, 1)}
    report["wall_s"] = round(time.time() - t0, 1)
    print(json.dumps(report, indent=1, default=str))

    # Save rows (input to calibrate.py) and log
    RUNS.mkdir(exist_ok=True)
    out = RUNS / f"e2e_{mode}_{args.split}_{time.strftime('%Y%m%d_%H%M')}.jsonl"
    out.write_text("\n".join(json.dumps(r, default=str) for r in rows))
    print(f"rows → {out}")
    flat = {f"{k}.{m}": v for k, d in report.items() if isinstance(d, dict) for m, v in d.items()}
    _log_mlflow(f"evalify_e2e_{mode}", {f"{mode}:{args.split}": {**flat, "version": mode, "family": ""}}, {}, out, args)


if __name__ == "__main__":
    main()
