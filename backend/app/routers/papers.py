# papers.py — exam papers: CRUD, file uploads, answer-key and rubric extraction.
# Static paths (/available, /files, /extract-*) are declared before /{paper_id}.

from __future__ import annotations

import os
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.db.mongodb import papers_col, submissions_col
from app.models.paper import PaperCreate, PaperOut
from app.routers.auth import get_current_user, require_teacher

router = APIRouter(prefix="/papers", tags=["papers"])
PAPER_UPLOAD_DIR = "uploads/papers"
_ALLOWED = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


class ExtractRequest(BaseModel):
    file_url: str     # from /papers/files/upload
    mcq_count: int


class ExtractRubricRequest(BaseModel):
    detailed_answer_url: str
    grade_rubric_url: str
    subjective_count: int


def _to_dict(doc: dict) -> dict:
    """Mongo doc → JSON-safe dict with a string id."""
    doc["id"] = str(doc.pop("_id"))
    doc.setdefault("resultCount", 0)
    doc.setdefault("createdAt", "")
    return doc


def _upload_path(url: str) -> str:
    """'/api/papers/files/<name>' → local path of that uploaded file."""
    return os.path.join(PAPER_UPLOAD_DIR, url.rstrip("/").split("/")[-1])


def _valid_id(paper_id: str) -> ObjectId:
    """400 on a malformed id."""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID format.")
    return ObjectId(paper_id)


@router.post("", response_model=PaperOut)
async def create_paper(body: PaperCreate, user: dict = Depends(require_teacher)):
    """Create a paper; subject is forced to the teacher's own subject."""
    doc = body.model_dump()
    doc.update(teacher_id=user["sub"], subject=user.get("subject", doc.get("subject", "")),
               createdAt=datetime.now(timezone.utc).isoformat(), resultCount=0)
    doc["_id"] = (await papers_col().insert_one(doc)).inserted_id
    return _to_dict(doc)


@router.get("")
async def list_papers(user: dict = Depends(require_teacher)):
    """The teacher's papers, newest first, with evaluated-submission counts."""
    papers = []
    async for doc in papers_col().find({"teacher_id": user["sub"]}).sort("createdAt", -1):
        doc["resultCount"] = await submissions_col().count_documents(
            {"paper_id": str(doc["_id"]), "status": "evaluated"})
        papers.append(_to_dict(doc))
    return papers


@router.get("/available")
async def available_papers(user: dict = Depends(get_current_user)):
    """All papers, each with this student's submission status."""
    papers = []
    async for doc in papers_col().find().sort("createdAt", -1):
        paper = _to_dict(doc)
        sub = await submissions_col().find_one({"student_id": user["sub"], "paper_id": paper["id"]})
        paper["submissionStatus"] = sub["status"] if sub else "not_submitted"
        paper["submissionId"] = str(sub["_id"]) if sub else None
        papers.append(paper)
    return papers


@router.post("/files/upload")
async def upload_paper_file(file: UploadFile = File(...), user: dict = Depends(require_teacher)):
    """Store a PDF/JPEG/PNG (≤ 20 MB) and return its server URL."""
    ext = os.path.splitext((file.filename or "").lower())[1]
    if ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Only PDF, JPEG, or PNG files are accepted.")
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")
    os.makedirs(PAPER_UPLOAD_DIR, exist_ok=True)
    name = f"{ObjectId()}{ext}"
    with open(os.path.join(PAPER_UPLOAD_DIR, name), "wb") as fh:
        fh.write(content)
    return {"url": f"/api/papers/files/{name}", "original_name": file.filename}


@router.get("/files/{filename}")
async def serve_paper_file(filename: str):
    """Serve an uploaded file (unguessable ObjectId name, no auth)."""
    ext = os.path.splitext(filename)[1].lower()
    if "/" in filename or ".." in filename or ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    path = os.path.join(PAPER_UPLOAD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, media_type=_ALLOWED[ext], filename=filename)


@router.post("/extract-answers")
async def extract_answers(body: ExtractRequest, user: dict = Depends(require_teacher)):
    """Pull MCQ answers out of an uploaded answer-key PDF for the teacher to review."""
    if body.mcq_count < 1:
        raise HTTPException(status_code=400, detail="mcq_count must be at least 1.")
    path = _upload_path(body.file_url)
    if not path.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file URL.")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found — upload the PDF first.")

    from app.services.pdf_utils import extract_mcq_answers_from_pdf
    answers, confidence, raw = extract_mcq_answers_from_pdf(path, body.mcq_count)
    return {"answers": answers, "confidence": round(confidence, 3),
            "extracted_count": len(answers), "raw_text_preview": raw[:500]}


@router.post("/extract-rubric")
async def extract_rubric(body: ExtractRubricRequest, user: dict = Depends(require_teacher)):
    """Build per-question rubrics from the detailed-answer and grade-rubric PDFs."""
    if body.subjective_count < 1:
        raise HTTPException(status_code=400, detail="subjective_count must be at least 1.")

    from app.services.rubric_extractor import extract_rubric_from_pdfs
    questions, rubrics, templates, warning = extract_rubric_from_pdfs(
        _upload_path(body.detailed_answer_url), _upload_path(body.grade_rubric_url), body.subjective_count)
    return {"subjective_questions": questions, "subjective_rubrics": rubrics,
            "subjective_prompt_templates": templates, "warning": warning}


@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(paper_id: str, user: dict = Depends(get_current_user)):
    """One paper (teachers and students)."""
    doc = await papers_col().find_one({"_id": _valid_id(paper_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return _to_dict(doc)


@router.delete("/{paper_id}")
async def delete_paper(paper_id: str, user: dict = Depends(require_teacher)):
    """Delete a paper the calling teacher owns."""
    res = await papers_col().delete_one({"_id": _valid_id(paper_id), "teacher_id": user["sub"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found or not owned by you.")
    return {"detail": "Paper deleted."}
