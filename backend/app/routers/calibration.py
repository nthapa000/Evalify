# calibration.py — optional, teacher-only calibration of subjective marks (V2 plan §3.4).
#
# The teacher hand-marks a few answer sheets (their marks are final for those sheets). "Apply" learns, per
# question, how much more generous the teacher is than the rubric grader (app/pipeline/calibration.py) and shifts
# the other students' subjective marks; rubric marks are kept next to the calibrated ones. Questions a TA or the
# teacher decided are never changed. New submissions of the paper are calibrated by the pipeline automatically.

from __future__ import annotations

from typing import Dict

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.mongodb import papers_col, submissions_col, users_col
from app.pipeline import calibration as cal
from app.routers.auth import require_teacher
from app.services import marks as M
from app.services.access import get_submission

router = APIRouter(prefix="/papers", tags=["calibration"])


async def _own_paper(paper_id: str, user: dict) -> dict:
    """The calling teacher's paper, or 404 (also for other teachers' papers)."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")
    paper = await papers_col().find_one({"_id": ObjectId(paper_id), "teacher_id": user["sub"]})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found or not owned by you.")
    return paper


def _subjective(sub: dict):
    """Subjective rows of a submission."""
    return sub.get("subjectiveDetail") or []


async def _rewrite(paper_id: str, fn) -> int:
    """Apply fn(row) to every unlocked subjective row of the paper's evaluated submissions; store + recompute."""
    n = 0
    async for sub in submissions_col().find({"paper_id": paper_id, "status": "evaluated"}):
        if sub.get("teacher_marks"):
            continue                                        # hand-marked sheets keep the teacher's marks
        rows = [dict(r) for r in _subjective(sub)]
        changed = False
        for r in rows:
            if not M.is_locked(r) and r.get("rubric_marks") is not None:
                changed |= fn(r)
        if changed:
            new = {**sub, "subjectiveDetail": rows}
            await submissions_col().update_one({"_id": sub["_id"]}, {"$set": {
                "subjectiveDetail": rows, "result": M.recompute(new)}})
            n += 1
    return n


class TeacherMarks(BaseModel):
    marks: Dict[str, float]


@router.put("/{paper_id}/calibration/marks/{submission_id}")
async def hand_mark(paper_id: str, submission_id: str, body: TeacherMarks, user: dict = Depends(require_teacher)):
    """The teacher's own marks for a sheet's subjective answers: final for that sheet, used for calibration."""
    await _own_paper(paper_id, user)
    sub = await get_submission(submission_id)
    if sub.get("paper_id") != paper_id or sub.get("status") != "evaluated":
        raise HTTPException(status_code=409, detail="This submission is not an evaluated sheet of this paper.")
    me = await users_col().find_one({"_id": ObjectId(user["sub"])})
    by = {"role": "teacher", "id": user["sub"], "name": (me or {}).get("name", "")}
    try:
        updates, history = M.apply_marks(sub, body.marks, by, source="teacher_marking", only_kind="subjective")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    teacher_marks = {**(sub.get("teacher_marks") or {}), **{q: float(v) for q, v in body.marks.items()}}
    await submissions_col().update_one({"_id": sub["_id"]}, {"$set": {**updates, "teacher_marks": teacher_marks},
                                                            "$push": {"marks_history": {"$each": history}}})
    return {"id": submission_id, "teacher_marks": teacher_marks, "result": updates["result"]}


@router.post("/{paper_id}/calibration/apply")
async def apply_calibration(paper_id: str, user: dict = Depends(require_teacher)):
    """Learn the per-question shift from the hand-marked sheets and apply it to every other sheet."""
    await _own_paper(paper_id, user)
    pairs, sheets = [], 0
    async for sub in submissions_col().find({"paper_id": paper_id, "teacher_marks": {"$exists": True}}):
        sheets += 1
        for r in _subjective(sub):
            q = r["question"]
            if q in sub["teacher_marks"] and r.get("rubric_marks") is not None:
                pairs.append((q, float(r["rubric_marks"]), float(sub["teacher_marks"][q])))
    if not pairs:
        raise HTTPException(status_code=409, detail="Hand-mark at least one answer sheet first (5–10 recommended).")
    fitted = cal.fit(pairs)
    await papers_col().update_one({"_id": ObjectId(paper_id)}, {"$set": {"calibration": fitted}})

    # Shift every unlocked subjective row of the other sheets: calibrated = rubric mark + this question's shift
    def shift(r):
        new = cal.apply(fitted, r["question"], float(r["rubric_marks"]), float(r.get("marks_available") or 0))
        changed = new != r.get("marks_earned") or r.get("calibrated_marks") != new
        r["calibrated_marks"], r["marks_earned"] = new, new
        return changed

    updated = await _rewrite(paper_id, shift)
    return {"answers": len(pairs), "sheets": sheets, "global": fitted["global"],
            "per_question": fitted["per_question"], "updated_submissions": updated}


@router.delete("/{paper_id}/calibration")
async def remove_calibration(paper_id: str, user: dict = Depends(require_teacher)):
    """Turn calibration off: unlocked subjective rows go back to the rubric marks."""
    await _own_paper(paper_id, user)
    await papers_col().update_one({"_id": ObjectId(paper_id)}, {"$unset": {"calibration": ""}})

    def revert(r):
        changed = r.get("calibrated_marks") is not None
        r["calibrated_marks"], r["marks_earned"] = None, float(r["rubric_marks"])
        return changed

    return {"updated_submissions": await _rewrite(paper_id, revert)}
