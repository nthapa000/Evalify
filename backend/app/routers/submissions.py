# submissions.py — students upload answer sheets; evaluation runs in the background.

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.db.mongodb import papers_col, submissions_col, users_col
from app.models.submission import SubmissionOut, SubmissionStatusOut
from app.routers.auth import get_current_user, require_student

router = APIRouter(prefix="/submissions", tags=["submissions"])
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}   # images only — phone photos of the sheet


async def _get_submission(submission_id: str) -> dict:
    """Fetch a submission or raise 400/404."""
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID.")
    doc = await submissions_col().find_one({"_id": ObjectId(submission_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return doc


@router.post("", response_model=SubmissionOut)
async def submit_paper(background_tasks: BackgroundTasks,
                       paper_id: str = Query(..., description="MongoDB _id of the exam paper"),
                       sheet_type: str = Query("omr", description="'omr' or 'handwritten'"),
                       files: List[UploadFile] = File(...),
                       current_user: dict = Depends(require_student)):
    """Save one or more page images and start evaluation in the background."""
    # Validate inputs
    if sheet_type not in ("omr", "handwritten"):
        raise HTTPException(status_code=400, detail="sheet_type must be 'omr' or 'handwritten'.")
    if not files:
        raise HTTPException(status_code=400, detail="At least one image file is required.")
    for f in files:
        ext = os.path.splitext((f.filename or "").lower())[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400,
                                detail=f"Unsupported file type '{ext}'. Upload PNG or JPG images only (no PDF).")
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID.")
    paper = await papers_col().find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    student = await users_col().find_one({"_id": ObjectId(current_user["sub"])})

    # Save pages in upload order as uploads/<sub_id>_p<i><ext>
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    sub_id, paths = ObjectId(), []
    for i, upload in enumerate(files):
        ext = os.path.splitext((upload.filename or "").lower())[1] or ".jpg"
        path = os.path.join(UPLOAD_DIR, f"{sub_id}_p{i}{ext}")
        with open(path, "wb") as fh:
            fh.write(await upload.read())
        paths.append(path)

    # Create the submission record, then queue evaluation
    doc = {
        "_id": sub_id, "paper_id": paper_id, "paper_name": paper["name"],
        "student_id": current_user["sub"], "student_name": student["name"] if student else "Unknown",
        "roll_no": current_user["roll_no"], "file_path": paths[0], "file_paths": paths,
        "file_ext": os.path.splitext(paths[0])[1], "page_count": len(paths), "sheet_type": sheet_type,
        "status": "processing", "submittedAt": datetime.now(timezone.utc).isoformat(), "result": None,
    }
    await submissions_col().insert_one(doc)
    from app.services.evaluator import evaluate_submission
    background_tasks.add_task(evaluate_submission, str(sub_id))
    return {**doc, "id": str(sub_id)}


@router.get("/{submission_id}/file")
async def get_submission_file(submission_id: str, user: dict = Depends(get_current_user)):
    """Serve the first page to its student or to any teacher."""
    doc = await _get_submission(submission_id)
    if user["role"] == "student" and doc["student_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    path = doc.get("file_path", "")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Answer sheet file not found on server.")
    ext = doc.get("file_ext", os.path.splitext(path)[1]).lower()
    mime = {".pdf": "application/pdf", ".png": "image/png"}.get(ext, "image/jpeg")
    return FileResponse(path, media_type=mime, filename=f"answer_sheet_{submission_id}{ext}")


@router.get("/{submission_id}/status", response_model=SubmissionStatusOut)
async def get_submission_status(submission_id: str, user: dict = Depends(get_current_user)):
    """Poll status; includes the result once evaluated."""
    doc = await _get_submission(submission_id)
    return {"id": str(doc["_id"]), "status": doc["status"], "result": doc.get("result")}
