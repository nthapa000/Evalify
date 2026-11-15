# results.py — evaluated results: per paper (teacher) and per submission (student, teacher, TA).

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.db.mongodb import papers_col, submissions_col
from app.routers.auth import get_current_user, require_teacher
from app.services.access import require_view

router = APIRouter(prefix="/results", tags=["results"])

# Never shown to students: TA identity, pipeline internals, TA review bookkeeping
STUDENT_HIDDEN = ("review", "pipeline", "ta_review", "teacher_marks", "file_path", "file_paths")


async def _scores(paper_id: str) -> tuple[list, list]:
    """All evaluated submissions for a paper and their total scores."""
    subs, scores = [], []
    async for doc in submissions_col().find({"paper_id": paper_id, "status": "evaluated"}):
        doc["id"] = str(doc.pop("_id"))
        subs.append(doc)
        if doc.get("result"):
            scores.append(doc["result"]["totalScore"])
    return subs, scores


@router.get("/paper/{paper_id}")
async def paper_results(paper_id: str, user: dict = Depends(require_teacher)):
    """Teacher view: every evaluated submission (with TA / re-evaluation status) + count/average/highest/lowest."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")
    paper = await papers_col().find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if paper.get("teacher_id") != user["sub"]:
        raise HTTPException(status_code=403, detail="Not your paper.")
    subs, s = await _scores(paper_id)
    return {"submissions": subs, "calibration": paper.get("calibration"), "stats": {
        "count": len(s), "average": round(sum(s) / len(s), 1) if s else 0,
        "highest": max(s, default=0), "lowest": min(s, default=0)}}


@router.get("/{submission_id}")
async def get_result(submission_id: str, user: dict = Depends(get_current_user)):
    """One result with its paper, class average/highest, marks history and re-evaluation state."""
    sub, paper = await require_view(user, submission_id)
    if not sub.get("result"):
        raise HTTPException(status_code=404, detail="Result not available yet.")
    sub["id"] = str(sub.pop("_id"))
    sub.setdefault("marks_history", [])
    sub.setdefault("reevaluation", None)
    if paper:
        paper["id"] = str(paper.pop("_id"))

    # Students see what changed and by which role, not who (TA names stay internal)
    if user.get("role") == "student":
        for k in STUDENT_HIDDEN:
            sub.pop(k, None)
        sub["marks_history"] = [{k: v for k, v in h.items() if k not in ("by_id", "by_name")}
                                for h in sub["marks_history"]]

    # Peer stats (fall back to own score if alone)
    own = sub["result"]["totalScore"]
    _, s = await _scores(sub["paper_id"])
    stats = {"average": round(sum(s) / len(s), 1) if s else own, "highest": max(s, default=own)}
    return {**sub, "paper": paper, "stats": stats}
