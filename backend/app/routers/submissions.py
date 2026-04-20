# submissions.py — Router for student answer-sheet submissions.
# POST /submissions             — upload answer sheet (creates a "processing" submission)
# GET  /submissions/{id}/status — poll until status == "evaluated"

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime, timezone
import asyncio
import random

from app.db.mongodb import submissions_col, papers_col
from app.routers.auth import require_student, get_current_user

router = APIRouter(prefix="/submissions", tags=["submissions"])


# ── Helper: convert MongoDB doc → dict with string id ────────────────────────

def _sub_to_dict(doc: dict) -> dict:
    """Convert a MongoDB submission document to a JSON-safe dictionary."""
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── Mock evaluation — simulates ML grading after a delay ─────────────────────
# In Phase 3+, this will be replaced by real OMR/TrOCR/LLM pipeline calls.

async def _run_mock_evaluation(submission_id: str, paper_id: str):
    """Background task: wait 4s, then set status='evaluated' with random score."""
    await asyncio.sleep(4)

    paper = await papers_col().find_one({"_id": ObjectId(paper_id)})
    max_score = paper["totalMarks"] if paper else 40
    total_score = round(max_score * (0.5 + random.random() * 0.45))

    result = {
        "mcqScore": round(total_score * 0.6),
        "numericalScore": round(total_score * 0.2) if paper and paper.get("numericalCount") else 0,
        "subjectiveScore": round(total_score * 0.2) if paper and paper.get("subjectiveCount") else 0,
        "totalScore": total_score,
        "maxScore": max_score,
        "percentage": round((total_score / max_score) * 100, 1),
    }

    # Update the submission document in MongoDB
    await submissions_col().update_one(
        {"_id": ObjectId(submission_id)},
        {"$set": {"status": "evaluated", "result": result}},
    )


# ── POST /submissions — submit answer sheet ──────────────────────────────────

@router.post("")
async def submit_answer_sheet(paper_id: str, user: dict = Depends(require_student)):
    """
    Create a new submission for the given paper.
    In Phase 2 this uses mock evaluation; Phase 3+ will use real ML.
    """
    # Validate paper exists
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")
    paper = await papers_col().find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    # Look up the student's name from the JWT (or fetch from users collection)
    from app.db.mongodb import users_col
    student = await users_col().find_one({"_id": ObjectId(user["sub"])})
    student_name = student["name"] if student else "Unknown"
    roll_no = student.get("roll_no", "") if student else ""

    # Create submission document with status "processing"
    doc = {
        "student_id": user["sub"],
        "student_name": student_name,
        "roll_no": roll_no,
        "paper_id": str(paper["_id"]),
        "paper_name": paper["name"],
        "status": "processing",
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "result": None,
    }
    result = await submissions_col().insert_one(doc)
    sub_id = str(result.inserted_id)

    # Fire-and-forget mock evaluation in the background
    asyncio.create_task(_run_mock_evaluation(sub_id, str(paper["_id"])))

    doc["id"] = sub_id
    del doc["_id"]  # may not exist as top-level key after insert_one
    return doc


# ── GET /submissions/{id}/status — poll evaluation status ────────────────────

@router.get("/{submission_id}/status")
async def submission_status(submission_id: str, user: dict = Depends(get_current_user)):
    """Return current status of a submission (processing/evaluated)."""
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")
    doc = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return {
        "id": str(doc["_id"]),
        "status": doc["status"],
        "result": doc.get("result"),
    }
