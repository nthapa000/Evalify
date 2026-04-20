# papers.py — CRUD router for exam papers.
# POST   /papers                  — create a paper (teacher)
# GET    /papers                  — list teacher's papers
# GET    /papers/available        — papers available to students
# POST   /papers/files/upload     — upload a PDF, return persistent server URL
# GET    /papers/files/{filename} — serve an uploaded PDF
# POST   /papers/extract-answers  — extract MCQ answers from an uploaded PDF
# GET    /papers/{id}             — get single paper
# DELETE /papers/{id}             — delete a paper (teacher)

from __future__ import annotations
import os

from bson import ObjectId
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, File, HTTPException, Depends, UploadFile
from fastapi.responses import FileResponse

from app.db.mongodb import papers_col, submissions_col
from app.models.paper import PaperCreate, PaperOut
from app.routers.auth import get_current_user, require_teacher

router = APIRouter(prefix="/papers", tags=["papers"])

PAPER_UPLOAD_DIR = "uploads/papers"


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
    """Create a new exam paper. Subject is locked to the teacher's assigned subject."""
    doc = body.model_dump()
    doc["teacher_id"] = user["sub"]
    doc["subject"] = user.get("subject", doc.get("subject", ""))
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
        count = await submissions_col().count_documents({
            "paper_id": str(doc["_id"]),
            "status": "evaluated",
        })
        doc["resultCount"] = count
        papers.append(_paper_to_dict(doc))
    return papers


# ── GET /papers/available — papers for students ──────────────────────────────
# Registered BEFORE /{paper_id} so "available" is not matched as a paper ID.

@router.get("/available")
async def available_papers(user: dict = Depends(get_current_user)):
    """Return all papers with the student's submission-status overlay."""
    cursor = papers_col().find().sort("createdAt", -1)
    papers = []
    async for doc in cursor:
        paper = _paper_to_dict(doc)
        sub = await submissions_col().find_one({
            "student_id": user["sub"],
            "paper_id": paper["id"],
        })
        paper["submissionStatus"] = sub["status"] if sub else "not_submitted"
        paper["submissionId"] = str(sub["_id"]) if sub else None
        papers.append(paper)
    return papers


# ── POST /papers/files/upload — upload a PDF for a paper ─────────────────────
# Registered BEFORE /{paper_id} so "files" is not matched as a paper ID.

@router.post("/files/upload")
async def upload_paper_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_teacher),
):
    """
    Upload a PDF (question paper, answer key, or answer sheet reference).
    Returns a persistent server URL to store in the paper document.
    Max size: 20 MB.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")

    os.makedirs(PAPER_UPLOAD_DIR, exist_ok=True)
    file_id = str(ObjectId())
    file_path = os.path.join(PAPER_UPLOAD_DIR, f"{file_id}.pdf")
    with open(file_path, "wb") as fh:
        fh.write(content)

    return {"url": f"/api/papers/files/{file_id}.pdf", "original_name": file.filename}


# ── GET /papers/files/{filename} — serve an uploaded PDF ─────────────────────

@router.get("/files/{filename}")
async def serve_paper_file(filename: str):
    """
    Serve a previously uploaded paper PDF.
    No auth required — files are named by unguessable UUID.
    """
    # Guard against path traversal
    if not filename.endswith(".pdf") or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(PAPER_UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(file_path, media_type="application/pdf", filename=filename)


class ExtractRequest(BaseModel):
    file_url: str   # server URL from /papers/files/upload, e.g. /api/papers/files/xxx.pdf
    mcq_count: int  # number of MCQ questions to look for


# ── POST /papers/extract-answers — extract MCQ answers from an uploaded PDF ───
# Registered BEFORE /{paper_id} so "extract-answers" is not matched as a paper ID.

@router.post("/extract-answers")
async def extract_answers(
    body: ExtractRequest,
    user: dict = Depends(require_teacher),
):
    """
    Extract MCQ answers from a previously uploaded answer key PDF.
    Accepts JSON: { file_url, mcq_count }.
    The teacher reviews and edits the result before saving the paper.
    """
    if body.mcq_count < 1:
        raise HTTPException(status_code=400, detail="mcq_count must be at least 1.")

    filename = body.file_url.rstrip("/").split("/")[-1]
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file URL.")

    file_path = os.path.join(PAPER_UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found — upload the PDF first.")

    from app.services.pdf_extractor import extract_mcq_answers_from_pdf
    answers, confidence, raw_text = extract_mcq_answers_from_pdf(file_path, body.mcq_count)

    return {
        "answers": answers,
        "confidence": round(confidence, 3),
        "extracted_count": len(answers),
        "raw_text_preview": raw_text[:500] if raw_text else "",
    }


# ── GET /papers/{paper_id} — single paper detail ────────────────────────────

@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(paper_id: str, user: dict = Depends(get_current_user)):
    """Return full paper detail. Both teacher and student roles can access this."""
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
        "teacher_id": user["sub"],
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found or not owned by you.")
    return {"detail": "Paper deleted."}
