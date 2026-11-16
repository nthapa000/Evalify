# evaluation.py — the teacher's "Start evaluation" for a paper and its progress (app/services/batch_runner.py).

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.db.mongodb import papers_col
from app.routers.auth import require_teacher
from app.services import batch_runner

router = APIRouter(prefix="/papers", tags=["evaluation"])


async def _own_paper(paper_id: str, user: dict) -> dict:
    """The teacher's own paper, or 404 (also for someone else's paper)."""
    paper = await papers_col().find_one({"_id": ObjectId(paper_id), "teacher_id": user["sub"]}) \
        if ObjectId.is_valid(paper_id) else None
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found or not owned by you.")
    return paper


@router.post("/{paper_id}/evaluate")
async def start_evaluation(paper_id: str, user: dict = Depends(require_teacher)):
    """Evaluate every submitted answer sheet of the paper as one batch (runs in the background)."""
    paper = await _own_paper(paper_id, user)
    try:
        batch = await batch_runner.start(paper, user["sub"])
    except batch_runner.BatchError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    batch_runner.kick(batch["id"])
    return batch


@router.get("/{paper_id}/evaluation")
async def evaluation_status(paper_id: str, user: dict = Depends(require_teacher)):
    """How many sheets wait for evaluation, and the stage / counts of the latest batch."""
    await _own_paper(paper_id, user)
    return await batch_runner.progress(paper_id)
