#!/usr/bin/env python3
"""grader_bakeoff.py — Phase 3: compare graders on GOLD transcripts (reading errors removed).

    python eval/grader_bakeoff.py eval/data/<set> [--split dev] [--thinking]

Every live JSON-capable model grades each gold subjective answer per concept.
Reports per grader: per-concept accuracy (vs gold concept labels), QWK / MAE /
exact / within-1 agreement with gold marks, evidence-not-found rate and latency.
Logs to MLflow experiment evalify_bakeoff_graders and eval/runs/graders_<time>.csv.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline import quality, readers  # noqa: E402
from app.pipeline.grader import grade  # noqa: E402
import dataset  # noqa: E402
import metrics  # noqa: E402
from reader_bakeoff import RUNS, _log_mlflow, live_endpoints  # noqa: E402


def subjective_items(sheets) -> list:
    """(sheet, question index, gold, crop images) for every gold subjective answer."""
    out = []
    for sh in sheets:
        pages = None
        for q in readers.questions_for(sh.paper):
            g = sh.gold.get(q.id)
            if q.kind != "subjective" or not g or "transcript" not in g:
                continue
            pages = pages or [quality.prepare(p)[0] for p in sh.pages]
            box = sh.crop_box(q.id)
            imgs = [readers._crop(pages[box["page"]], box["bbox"])] if box else pages
            out.append((sh, int(q.id[1:]) - 1, g, imgs))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--thinking", action="store_true", help="enable Qwen thinking mode")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    items = subjective_items(dataset.load(args.set_dir, args.split))
    graders = [e for e in live_endpoints() if e.spec.get("supports_json_schema")]
    print(f"{len(items)} gold subjective answers; graders: {[g.name for g in graders]}")

    results = {}
    for ep in graders:
        def one(it):
            sh, i, g, imgs = it
            rubric = (sh.paper.get("subjectiveRubrics") or [{}] * (i + 1))[i]
            question = (sh.paper.get("subjectiveQuestions") or [""] * (i + 1))[i]
            # Gold transcript as BOTH transcripts: isolates grading from reading
            return g, grade(ep, question, rubric, g["transcript"], g["transcript"], imgs,
                            sh.paper.get("subject", ""), thinking=args.thinking)

        t0 = time.time()
        with ThreadPoolExecutor(args.workers) as pool:
            done = list(pool.map(one, items))

        # Marks agreement with gold + per-concept accuracy where gold concept labels exist
        gold_m = [g["marks"] for g, _ in done if "marks" in g]
        pred_m = [r.marks for g, r in done if "marks" in g]
        concept_hits = [d.present == g["concepts"][d.concept] for g, r in done
                        for d in r.decisions if d.concept in g.get("concepts", {})]
        decisions = [d for _, r in done for d in r.decisions]
        key = f"{ep.name}{':thinking' if args.thinking else ''}"
        results[key] = {
            "n": len(done), "version": ep.version, "family": ep.spec.get("family"),
            "qwk": metrics.qwk(gold_m, pred_m), "mae": metrics.mae(gold_m, pred_m),
            "exact": metrics.agreement(gold_m, pred_m, 0), "within_1": metrics.agreement(gold_m, pred_m, 1),
            "concept_acc": sum(concept_hits) / len(concept_hits) if concept_hits else float("nan"),
            "evidence_missing_rate": sum(not d.evidence_found for d in decisions) / max(1, len(decisions)),
            "errors": sum(bool(r.error) for _, r in done),
            "latency_mean_s": sum(r.latency_s for _, r in done) / max(1, len(done)),
            "wall_s": round(time.time() - t0, 1),
        }
        print(key, {k: round(v, 3) if isinstance(v, float) else v for k, v in results[key].items()})

    # Leaderboard + MLflow
    RUNS.mkdir(exist_ok=True)
    out = RUNS / f"graders_{time.strftime('%Y%m%d_%H%M')}.csv"
    cols = sorted({c for r in results.values() for c in r})
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["grader"] + cols)
        for k, r in results.items():
            w.writerow([k] + [r.get(c, "") for c in cols])
    print(f"leaderboard → {out}")
    _log_mlflow("evalify_bakeoff_graders", results, {}, out, args)


if __name__ == "__main__":
    main()
