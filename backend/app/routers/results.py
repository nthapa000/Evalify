# results.py — evaluated results: per paper (teacher) and per submission (student).

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.db.mongodb import papers_col, submissions_col
from app.routers.auth import get_current_user, require_teacher

router = APIRouter(prefix="/results", tags=["results"])


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
    """Teacher view: every evaluated submission + count/average/highest/lowest."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")
    subs, s = await _scores(paper_id)
    return {"submissions": subs, "stats": {
        "count": len(s), "average": round(sum(s) / len(s), 1) if s else 0,
        "highest": max(s, default=0), "lowest": min(s, default=0)}}


@router.get("/{submission_id}")
async def get_result(submission_id: str, user: dict = Depends(get_current_user)):
    """One result with its paper and class average/highest."""
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")
    sub = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if not sub.get("result"):
        raise HTTPException(status_code=404, detail="Result not available yet.")
    sub["id"] = str(sub.pop("_id"))

    # Attach the paper for context
    paper = None
    if ObjectId.is_valid(sub.get("paper_id", "")):
        paper = await papers_col().find_one({"_id": ObjectId(sub["paper_id"])})
        if paper:
            paper["id"] = str(paper.pop("_id"))

    # Peer stats (fall back to own score if alone)
    own = sub["result"]["totalScore"]
    _, s = await _scores(sub["paper_id"])
    stats = {"average": round(sum(s) / len(s), 1) if s else own, "highest": max(s, default=own)}
    return {**sub, "paper": paper, "stats": stats}
