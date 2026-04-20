# submissions.py — REST endpoints for student answer-sheet submissions.
#
# POST /submissions                — student uploads an answer sheet (PDF or image).
# GET  /submissions/{id}/status   — poll evaluation progress.
# GET  /submissions/{id}/file     — serve the uploaded answer sheet for viewing.

from __future__ import annotations
import os
from datetime import datetime, timezone

from bson import ObjectId
from typing import List

from fastapi import (
    APIRouter, BackgroundTasks, Depends,
    File, HTTPException, Query, UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse

from app.db.mongodb import papers_col, submissions_col, users_col
from app.models.submission import SubmissionOut, SubmissionStatusOut
from app.routers.auth import get_current_user, require_student

router = APIRouter(prefix="/submissions", tags=["submissions"])

UPLOAD_DIR = "uploads"

# Images only — PDF removed (camera photos cause OMR accuracy issues)
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_MIMES = {"image/png", "image/jpeg"}


# ── POST /submissions ──────────────────────────────────────────────────────────

@router.post("", response_model=SubmissionOut)
async def submit_paper(
    background_tasks: BackgroundTasks,
    paper_id:   str = Query(...,   description="MongoDB _id of the exam paper"),
    sheet_type: str = Query("omr", description="'omr' or 'handwritten'"),
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(require_student),
):
    """
    Accept one or more answer-sheet images (PNG/JPG) and kick off evaluation.
    Multiple images are supported for multi-page answer sheets.
    """
    if sheet_type not in ("omr", "handwritten"):
        raise HTTPException(status_code=400, detail="sheet_type must be 'omr' or 'handwritten'.")

    if not files:
        raise HTTPException(status_code=400, detail="At least one image file is required.")

    # Validate all files up front
    for f in files:
        fname = (f.filename or "").lower()
        ext = os.path.splitext(fname)[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Upload PNG or JPG images only (no PDF)."
            )

    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")
    paper = await papers_col().find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    student = await users_col().find_one({"_id": ObjectId(current_user["sub"])})
    student_name = student["name"] if student else "Unknown"

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save all uploaded images; track paths in order (page 1, page 2, …)
    sub_id = ObjectId()
    file_paths = []
    for idx, upload in enumerate(files):
        fname = (upload.filename or "").lower()
        ext   = os.path.splitext(fname)[1] or ".jpg"
        path  = os.path.join(UPLOAD_DIR, f"{sub_id}_p{idx}{ext}")
        content = await upload.read()
        with open(path, "wb") as fh:
            fh.write(content)
        file_paths.append(path)

    # file_path = first page (for backward-compat serve endpoint)
    # file_paths = full ordered list for multi-page evaluation
    sub_doc = {
        "_id":          sub_id,
        "paper_id":     paper_id,
        "paper_name":   paper["name"],
        "student_id":   current_user["sub"],
        "student_name": student_name,
        "roll_no":      current_user["roll_no"],
        "file_path":    file_paths[0],
        "file_paths":   file_paths,
        "file_ext":     os.path.splitext(file_paths[0])[1],
        "page_count":   len(file_paths),
        "sheet_type":   sheet_type,
        "status":       "processing",
        "submittedAt":  datetime.now(timezone.utc).isoformat(),
        "result":       None,
    }
    await submissions_col().insert_one(sub_doc)

    from app.services.evaluator import evaluate_submission
    background_tasks.add_task(evaluate_submission, str(sub_id))

    return {**sub_doc, "id": str(sub_id)}


# ── GET /submissions/{id}/file — serve uploaded answer sheet ─────────────────
# Must come BEFORE /{id}/status so "file" segment isn't matched as status path.

@router.get("/{submission_id}/file")
async def get_submission_file(
    submission_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Serve the student's uploaded answer sheet (PDF or image).
    Only the submitting student or a teacher can access this.
    """
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")

    doc = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Allow: the student who submitted, or any teacher
    if user["role"] == "student" and doc["student_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    file_path = doc.get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Answer sheet file not found on server.")

    ext = doc.get("file_ext", os.path.splitext(file_path)[1]).lower()
    mime = "application/pdf" if ext == ".pdf" else "image/png" if ext == ".png" else "image/jpeg"

    return FileResponse(file_path, media_type=mime, filename=f"answer_sheet_{submission_id}{ext}")


# ── GET /submissions/{id}/status ──────────────────────────────────────────────

@router.get("/{submission_id}/status", response_model=SubmissionStatusOut)
async def get_submission_status(
    submission_id: str,
    user: dict = Depends(get_current_user),
):
    """Poll the evaluation status of a submission. Returns status + result when done."""
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")

    doc = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")

    return {
        "id":     str(doc["_id"]),
        "status": doc["status"],
        "result": doc.get("result"),
    }
