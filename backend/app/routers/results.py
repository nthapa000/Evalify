# results.py — Router for viewing evaluation results.
# GET /results/{submission_id}      — individual result (student)
# GET /results/paper/{paper_id}     — all results for a paper (teacher)

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.db.mongodb import submissions_col, papers_col
from app.routers.auth import get_current_user, require_teacher

router = APIRouter(prefix="/results", tags=["results"])


# ── GET /results/paper/{paper_id} — teacher view ────────────────────────────
# Must be before /results/{submission_id} to avoid route collision

@router.get("/paper/{paper_id}")
async def paper_results(paper_id: str, user: dict = Depends(require_teacher)):
    """Return all evaluated submissions for a paper, with aggregate stats."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")

    # Find all evaluated submissions for this paper
    cursor = submissions_col().find({"paper_id": paper_id, "status": "evaluated"})
    subs = []
    scores = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        subs.append(doc)
        if doc.get("result"):
            scores.append(doc["result"]["totalScore"])

    # Compute aggregate stats
    stats = {
        "count": len(scores),
        "average": round(sum(scores) / len(scores), 1) if scores else 0,
        "highest": max(scores) if scores else 0,
        "lowest": min(scores) if scores else 0,
    }

    return {"submissions": subs, "stats": stats}


# ── GET /results/{submission_id} — individual result ─────────────────────────

@router.get("/{submission_id}")
async def get_result(submission_id: str, user: dict = Depends(get_current_user)):
    """Return full result for one submission, including peer stats."""
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")

    sub = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if not sub.get("result"):
        raise HTTPException(status_code=404, detail="Result not available yet.")

    sub["id"] = str(sub.pop("_id"))

    # Fetch the paper for context
    paper = None
    if ObjectId.is_valid(sub.get("paper_id", "")):
        paper_doc = await papers_col().find_one({"_id": ObjectId(sub["paper_id"])})
        if paper_doc:
            paper_doc["id"] = str(paper_doc.pop("_id"))
            paper = paper_doc

    # Compute peer stats (average + highest across all evaluated subs for this paper)
    peer_cursor = submissions_col().find({
        "paper_id": sub["paper_id"],
        "status": "evaluated",
    })
    peer_scores = []
    async for peer in peer_cursor:
        if peer.get("result"):
            peer_scores.append(peer["result"]["totalScore"])

    stats = {
        "average": round(sum(peer_scores) / len(peer_scores), 1) if peer_scores else sub["result"]["totalScore"],
        "highest": max(peer_scores) if peer_scores else sub["result"]["totalScore"],
    }

    return {**sub, "paper": paper, "stats": stats}
