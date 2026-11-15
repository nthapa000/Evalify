# access.py — who may see a submission: its student, the paper's teacher, or a TA of the paper's subject.

from __future__ import annotations

from bson import ObjectId
from fastapi import HTTPException

from app.db.mongodb import papers_col, submissions_col
from app.routers.auth import user_subjects


async def get_submission(submission_id: str) -> dict:
    """Fetch a submission or raise 400 (bad id) / 404."""
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")
    doc = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return doc


async def get_paper(paper_id: str) -> dict | None:
    """The paper of a submission (None if it was deleted)."""
    return await papers_col().find_one({"_id": ObjectId(paper_id)}) if ObjectId.is_valid(paper_id or "") else None


async def can_view(user: dict, sub: dict, paper: dict | None) -> bool:
    """Student: own submission. Teacher: owns the paper. TA: TA of the paper's subject."""
    role = user.get("role")
    if role == "student":
        return sub.get("student_id") == user.get("sub")
    if role == "teacher":
        return bool(paper) and paper.get("teacher_id") == user.get("sub")
    if role == "ta":
        return bool(paper) and paper.get("subject") in await user_subjects(user)
    return False


async def require_view(user: dict, submission_id: str) -> tuple[dict, dict | None]:
    """(submission, paper) or 403 when the caller may not see it."""
    sub = await get_submission(submission_id)
    paper = await get_paper(sub.get("paper_id", ""))
    if not await can_view(user, sub, paper):
        raise HTTPException(status_code=403, detail="Access denied.")
    return sub, paper
