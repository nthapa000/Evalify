# calibration.py — optional teacher calibration of subjective marks (per-question shift).
#
# The teacher hand-marks a few answer sheets (optional, teacher-only). For each question we learn how much more
# (or less) generous the teacher is than our rubric grader, and add that to the grader's mark. Both the rubric
# mark and the calibrated mark are kept. Measured on Mendeley (runs 9–10): with 10 teacher sheets MAE 0.61 → 0.38
# (marks out of 2), within 0.5 mark 55 % → 83 %. Alternative documented in V2_EVALIFY_PLAN.md: few-shot + shift.

from __future__ import annotations

from statistics import mean
from typing import Iterable, Optional, Tuple

SHRINK = 3.0        # a question with few teacher examples is pulled towards the overall shift


def fit(pairs: Iterable[Tuple[str, float, float]], shrink: float = SHRINK) -> dict:
    """pairs = [(question id, grader mark, teacher mark)] from the teacher-marked sheets →
    {"global": shift, "per_question": {qid: shift}, "n": count}."""
    pairs = list(pairs)
    if not pairs:
        raise ValueError("calibration needs at least one teacher-marked answer")
    overall = mean(t - g for _, g, t in pairs)
    by_q: dict = {}
    for q, g, t in pairs:
        by_q.setdefault(q, []).append(t - g)
    # shrunken mean: (sum of differences + shrink × overall) / (n + shrink)
    per_q = {q: (sum(d) + shrink * overall) / (len(d) + shrink) for q, d in by_q.items()}
    return {"global": overall, "per_question": per_q, "n": len(pairs)}


def apply(cal: Optional[dict], qid: str, mark: float, max_marks: float) -> float:
    """Grader mark + this question's shift, rounded to the nearest half mark and clipped to [0, max]."""
    if not cal:
        return mark
    shift = (cal.get("per_question") or {}).get(qid, cal.get("global", 0.0))
    return min(float(max_marks), max(0.0, round((mark + shift) * 2) / 2))
