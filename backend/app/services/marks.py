# marks.py — changing marks after evaluation (TA re-evaluation, teacher hand-marking, calibration).
#
# Every change goes through apply_marks(): it validates the marks, updates the question rows, locks the rows a
# person decided (TA / teacher marks are final), writes a history entry per changed question and recomputes the
# section scores and total. Pure functions on the submission dict — the routers store the returned updates.

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

DETAIL_KEYS = ("mcqDetail", "numericalDetail", "subjectiveDetail")
SECTION_SCORE = {"mcqDetail": "mcqScore", "numericalDetail": "numericalScore", "subjectiveDetail": "subjectiveScore"}


def kind_of(detail_key: str) -> str:
    """'mcqDetail' → 'mcq'."""
    return {"mcqDetail": "mcq", "numericalDetail": "numerical", "subjectiveDetail": "subjective"}[detail_key]


def rows(sub: dict):
    """(detail key, row) for every question row of a submission, in paper order."""
    for key in DETAIL_KEYS:
        for row in sub.get(key) or []:
            yield key, row


def is_locked(row: dict) -> bool:
    """A row a TA or teacher decided — final, never changed by calibration."""
    return bool(row.get("final_by"))


def recompute(sub: dict) -> dict:
    """New result dict from the per-question marks (the MCQ section never goes below zero, as at grading)."""
    result = dict(sub.get("result") or {})
    total = 0.0
    for key in DETAIL_KEYS:
        s = round(sum(float(r.get("marks_earned") or 0) for r in sub.get(key) or []), 3)
        if key == "mcqDetail":
            s = max(0.0, s)
        result[SECTION_SCORE[key]] = s
        total += s
    result["totalScore"] = round(total, 3)
    mx = float(result.get("maxScore") or 0)
    result["percentage"] = round(total / mx * 100, 1) if mx > 0 else 0.0
    return result


def apply_marks(sub: dict, marks: Dict[str, object], by: dict, remark: str = "", source: str = "",
                only_kind: Optional[str] = None) -> Tuple[dict, List[dict]]:
    """Validate and apply {question: new mark}. Returns ($set updates for the submission, new history entries).
    Raises ValueError on an unknown question, a non-number, or a mark outside 0…marks_available."""
    new = {k: copy.deepcopy(sub.get(k) or []) for k in DETAIL_KEYS}
    index = {r["question"]: (k, r) for k in DETAIL_KEYS for r in new[k]}
    now = datetime.now(timezone.utc).isoformat()
    history = []
    for q, value in marks.items():
        if q not in index:
            raise ValueError(f"{q}: no such question on this paper")
        key, row = index[q]
        if only_kind and kind_of(key) != only_kind:
            raise ValueError(f"{q}: only {only_kind} questions can be marked here")
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{q}: marks must be a number") from None
        mx = float(row.get("marks_available") or 0)
        if not 0 <= v <= mx:
            raise ValueError(f"{q}: marks must be between 0 and {mx:g}")
        old = float(row.get("marks_earned") or 0)
        row["final_by"] = by["role"]                       # a person decided this question: final
        if v != old:
            row["marks_earned"] = v
            history.append({"question": q, "old": old, "new": v, "by_role": by["role"], "by_id": by.get("id", ""),
                            "by_name": by.get("name", ""), "remark": remark, "source": source, "at": now})
    updates = dict(new)
    updates["result"] = recompute({**sub, **new})
    return updates, history
