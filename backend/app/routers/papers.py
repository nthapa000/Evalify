# papers.py — CRUD router for exam papers.
# POST   /papers           — create a paper (teacher)
# GET    /papers           — list teacher's papers
# GET    /papers/available — papers available to students
# GET    /papers/{id}      — get single paper
# DELETE /papers/{id}      — delete a paper (teacher)

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime, timezone

from app.db.mongodb import papers_col, submissions_col
from app.models.paper import PaperCreate, PaperOut, PaperListItem
from app.routers.auth import get_current_user, require_teacher

router = APIRouter(prefix="/papers", tags=["papers"])


# ── Helper: convert MongoDB doc → dict with string id ────────────────────────

def _paper_to_dict(doc: dict) -> dict:
    """Convert a MongoDB paper document to a JSON-safe dictionary."""
    doc["id"] = str(doc.pop("_id"))
    doc.setdefault("resultCount", 0)
    doc.setdefault("createdAt", "")
    return doc


# ── POST /papers — create paper ──────────────────────────────────────────────

@router.post("", response_model=PaperOut)
async def create_paper(body: PaperCreate, user: dict = Depends(require_teacher)):
    """Create a new exam paper. Only teachers can call this."""
    doc = body.model_dump()
    doc["teacher_id"] = user["sub"]           # link paper to the logged-in teacher
    doc["createdAt"] = datetime.now(timezone.utc).isoformat()
    doc["resultCount"] = 0

    result = await papers_col().insert_one(doc)
    doc["_id"] = result.inserted_id
    return _paper_to_dict(doc)


# ── GET /papers — list teacher's papers ──────────────────────────────────────

@router.get("")
async def list_papers(user: dict = Depends(require_teacher)):
    """Return all papers created by the logged-in teacher."""
    cursor = papers_col().find({"teacher_id": user["sub"]}).sort("createdAt", -1)
    papers = []
    async for doc in cursor:
        # Count evaluated submissions for each paper
        count = await submissions_col().count_documents({
            "paper_id": str(doc["_id"]),
            "status": "evaluated",
        })
        doc["resultCount"] = count
        papers.append(_paper_to_dict(doc))
    return papers


# ── GET /papers/available — papers for students ──────────────────────────────
# Must come BEFORE /papers/{paper_id} so FastAPI doesn't match "available" as an id

@router.get("/available")
async def available_papers(user: dict = Depends(get_current_user)):
    """Return all papers with the student's submission status overlay."""
    cursor = papers_col().find().sort("createdAt", -1)
    papers = []
    async for doc in cursor:
        paper = _paper_to_dict(doc)
        # Check if this student has already submitted for this paper
        sub = await submissions_col().find_one({
            "student_id": user["sub"],
            "paper_id": paper["id"],
        })
        paper["submissionStatus"] = sub["status"] if sub else "not_submitted"
        paper["submissionId"] = str(sub["_id"]) if sub else None
        papers.append(paper)
    return papers


# ── GET /papers/{paper_id} — single paper detail ────────────────────────────

@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(paper_id: str, user: dict = Depends(get_current_user)):
    """Return full paper detail. Both roles can access this."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID format.")
    doc = await papers_col().find_one({"_id": ObjectId(paper_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return _paper_to_dict(doc)


# ── DELETE /papers/{paper_id} — delete paper ─────────────────────────────────

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str, user: dict = Depends(require_teacher)):
    """Delete a paper. Only the teacher who created it can delete it."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID format.")
    result = await papers_col().delete_one({
        "_id": ObjectId(paper_id),
        "teacher_id": user["sub"],  # ensure teacher owns this paper
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found or not owned by you.")
    return {"detail": "Paper deleted."}
