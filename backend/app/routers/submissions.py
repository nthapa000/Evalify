# submissions.py — students upload answer sheets (evaluated in the background), view pages, ask for re-evaluation.

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from app.db.mongodb import papers_col, submissions_col, users_col
from app.models.submission import SubmissionOut, SubmissionStatusOut
from app.routers.auth import get_current_user, require_student, user_subjects
from app.services.access import require_view

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
    # Only students enrolled in the paper's subject may submit (enrolment from demo.env)
    subjects = await user_subjects(current_user)
    if subjects and paper.get("subject") not in subjects:
        raise HTTPException(status_code=403, detail="You are not enrolled in this paper's subject.")
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
    # The raw Mongo _id is not JSON; the API exposes it as "id"
    return {**{k: v for k, v in doc.items() if k != "_id"}, "id": str(sub_id)}


@router.get("/{submission_id}/file")
async def get_submission_file(submission_id: str, user: dict = Depends(get_current_user)):
    """Serve the first page to its student, the paper's teacher or a TA of the subject."""
    doc, _ = await require_view(user, submission_id)
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


# ── Pages (student, the paper's teacher, TAs of the subject) ─────────────────

def _pages(doc: dict) -> list:
    """Page files of a submission in upload order."""
    return doc.get("file_paths") or ([doc["file_path"]] if doc.get("file_path") else [])


@router.get("/{submission_id}/pages")
async def page_count(submission_id: str, user: dict = Depends(get_current_user)):
    """How many pages the answer sheet has (the viewer then loads /pages/{i})."""
    doc, _ = await require_view(user, submission_id)
    return {"count": len(_pages(doc))}


@router.get("/{submission_id}/pages/{index}")
async def page_file(submission_id: str, index: int, user: dict = Depends(get_current_user)):
    """One page image (0-based index)."""
    doc, _ = await require_view(user, submission_id)
    pages = _pages(doc)
    if not 0 <= index < len(pages) or not os.path.exists(pages[index]):
        raise HTTPException(status_code=404, detail="Page not found.")
    ext = os.path.splitext(pages[index])[1].lower()
    return FileResponse(pages[index], media_type="image/png" if ext == ".png" else "image/jpeg")


# ── Re-evaluation request (one per submission) ───────────────────────────────

class ReevaluationRequest(BaseModel):
    remark: str

    @field_validator("remark")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """The TA needs to know what to re-check."""
        v = (v or "").strip()
        if not v:
            raise ValueError("Please say which questions to re-check and why.")
        if len(v) > 2000:
            raise ValueError("Keep the remark under 2000 characters.")
        return v


@router.post("/{submission_id}/reevaluation")
async def request_reevaluation(submission_id: str, body: ReevaluationRequest,
                               user: dict = Depends(require_student)):
    """The student's one re-evaluation request for this paper; a TA of the subject answers it."""
    doc, _ = await require_view(user, submission_id)
    if doc.get("status") != "evaluated":
        raise HTTPException(status_code=409, detail="The paper has not been evaluated yet.")
    if doc.get("reevaluation"):
        raise HTTPException(status_code=409, detail="You have already asked for re-evaluation of this paper.")
    req = {"remark": body.remark, "status": "pending", "requestedAt": datetime.now(timezone.utc).isoformat()}
    await submissions_col().update_one({"_id": doc["_id"]}, {"$set": {"reevaluation": req}})
    return {"id": submission_id, "reevaluation": req}
