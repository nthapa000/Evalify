#!/usr/bin/env python3
"""calibrate.py — pick routing thresholds on the DEV split to hit a target auto-accept accuracy.

    python eval/calibrate.py eval/runs/e2e_pipeline_dev_<time>.jsonl --target 0.98 [--write]

Re-applies the confidence-based routing rules offline with candidate thresholds
(reader confidence, concept confidence, transcript similarity, grader gap) to the
saved per-question readings, keeps the settings whose auto-accepted accuracy ≥
target, and among those chooses the one with the highest coverage (fewest TA
checks). Rules that are not threshold-based (reader disagreement on exact
answers, failed pages, unparseable numbers) always stay on.
--write saves the result to infra/routing.yaml, which the backend reads.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import metrics  # noqa: E402
from app.pipeline.readers import text_similarity  # noqa: E402

ROUTING_YAML = Path(__file__).resolve().parents[1] / "infra" / "routing.yaml"
GRID = {
    "reader_min_confidence": [0.0, 0.5, 0.6, 0.7, 0.8, 0.9],
    "concept_min_confidence": [0.0, 0.5, 0.6, 0.7, 0.8, 0.9],
    "transcript_min_similarity": [0.7, 0.8, 0.85, 0.9, 0.95],
    "grader_max_mark_gap": [0.5, 1.0, 1.5, 2.0],
}
# Reasons controlled by the thresholds above (everything else is always routed)
TUNABLE = ("low reader confidence", "low confidence on", "transcripts differ", "graders differ")


def routed(row: dict, t: dict) -> bool:
    """Would this question be routed under thresholds t?"""
    fixed = [r for r in row["reasons"] if not r.startswith(TUNABLE)]
    if fixed:
        return True
    a = (row.get("readings") or {}).get("a") or {}
    if a.get("confidence") is not None and a["confidence"] < t["reader_min_confidence"]:
        return True
    for c in row.get("concepts") or []:
        if c.get("confidence") is not None and c["confidence"] < t["concept_min_confidence"]:
            return True
    # Subjective: recompute transcript similarity and grader gap from the raw values
    b = (row.get("readings") or {}).get("b") or {}
    if row["kind"] == "subjective" and b.get("value"):
        if text_similarity(a.get("value", ""), b["value"]) < t["transcript_min_similarity"]:
            return True
    g2 = row.get("second_grader_marks")
    if g2 is not None and abs(row["marks"] - g2) > t["grader_max_mark_gap"]:
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", help="e2e_pipeline_dev_*.jsonl from end_to_end.py (DEV split only)")
    ap.add_argument("--target", type=float, default=0.98, help="required accuracy on auto-accepted items")
    ap.add_argument("--write", action="store_true", help="save to infra/routing.yaml")
    args = ap.parse_args()
    if "_test_" in args.rows:
        sys.exit("calibrate on the dev split; the test split is only for the final report")
    rows = [json.loads(l) for l in Path(args.rows).read_text().splitlines() if l.strip()]

    # Grid search: maximise coverage subject to auto-accept accuracy ≥ target
    best = None
    for values in itertools.product(*GRID.values()):
        t = dict(zip(GRID, values))
        m = metrics.system_metrics([{"correct": r["correct"], "routed": routed(r, t)} for r in rows])
        if m["auto_accuracy"] == m["auto_accuracy"] and m["auto_accuracy"] >= args.target:   # not NaN
            if best is None or m["coverage"] > best[1]["coverage"]:
                best = (t, m)

    if best is None:
        print(f"no setting reaches {args.target:.0%} auto-accept accuracy on {len(rows)} items — "
              "route everything uncertain, or improve readers first")
        return
    t, m = best
    print("thresholds:", t)
    print(f"coverage {m['coverage']:.1%}  auto-accept accuracy {m['auto_accuracy']:.1%}  "
          f"silent errors {m['silent_error']:.1%}  routed {m['routing_rate']:.1%}  (n={m['items']})")
    if args.write:
        ROUTING_YAML.write_text(f"# calibrated by eval/calibrate.py on {Path(args.rows).name} "
                                f"(target {args.target})\n" + yaml.safe_dump(t))
        print(f"saved → {ROUTING_YAML}")


if __name__ == "__main__":
    main()
