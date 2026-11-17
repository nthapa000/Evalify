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
from app.routers.auth import get_current_user, require_teacher, user_subjects
from app.services.access import student_status

router = APIRouter(prefix="/papers", tags=["papers"])
PAPER_UPLOAD_DIR = "uploads/papers"
# .txt: plain reference notes for the answer-key assistant
_ALLOWED = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".txt": "text/plain"}


class ExtractRequest(BaseModel):
    file_url: str     # from /papers/files/upload
    mcq_count: int


class DetectQuestionsRequest(BaseModel):
    file_url: str     # question paper PDF from /papers/files/upload


class OmrTemplateRequest(BaseModel):
    blank_url: str               # blank OMR sheet image from /papers/files/upload
    mcq_count: int
    n_options: int | None = None # leave empty to detect


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
    """Create a paper; the subject must be one the teacher teaches (their first subject if none or another is given)."""
    doc = body.model_dump()
    # An OMR paper needs its blank sheet with the bubble map confirmed (an ignored template once scored a sheet 0)
    tpl = doc.get("omrTemplate") or {}
    if doc.get("type") == "mcq" and doc.get("answerSheetFormat") == "omr" and not (tpl.get("bubbles") and tpl.get("confirmed")):
        raise HTTPException(status_code=400, detail="An OMR paper needs its blank OMR sheet, with the detected bubbles confirmed.")
    mine = await user_subjects(user) or [user.get("subject", "")]
    subject = doc.get("subject") if doc.get("subject") in mine else mine[0]      # a teacher with two subjects picks one
    doc.update(teacher_id=user["sub"], subject=subject,
               createdAt=datetime.now(timezone.utc).isoformat(), resultCount=0,
               resultsReleased=False, releasedAt=None)          # students see marks only after release
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
    """Papers of the student's enrolled subjects, each with this student's submission status."""
    papers = []
    # Enrolment comes from demo.env; a user with no subjects listed (older data) sees every paper
    subjects = await user_subjects(user)
    query = {"subject": {"$in": subjects}} if subjects else {}
    async for doc in papers_col().find(query).sort("createdAt", -1):
        paper = _to_dict(doc)
        sub = await submissions_col().find_one({"student_id": user["sub"], "paper_id": paper["id"]})
        # "awaiting_release" until the teacher releases results (shown as "being evaluated")
        paper["submissionStatus"] = student_status(sub, doc) if sub else "not_submitted"
        paper["submissionId"] = str(sub["_id"]) if sub else None
        papers.append(paper)
    return papers


@router.post("/files/upload")
async def upload_paper_file(file: UploadFile = File(...), user: dict = Depends(require_teacher)):
    """Store a PDF/JPEG/PNG (≤ 20 MB) and return its server URL."""
    ext = os.path.splitext((file.filename or "").lower())[1]
    if ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Only PDF, JPEG, PNG or TXT files are accepted.")
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


@router.post("/detect-questions")
async def detect_questions(body: DetectQuestionsRequest, user: dict = Depends(require_teacher)):
    """Number of numbered questions in an uploaded question paper PDF (null when none are found, e.g. a scan)."""
    path = _upload_path(body.file_url)
    if not path.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file URL.")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found — upload the PDF first.")
    from app.services.pdf_utils import count_questions, pdf_extract_text
    return {"count": count_questions(pdf_extract_text(path)) or None}


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


@router.post("/omr-template")
async def omr_template(body: OmrTemplateRequest, user: dict = Depends(require_teacher)):
    """Learn the bubble map from a blank OMR sheet; returns it plus a labelled preview to confirm."""
    import asyncio
    import cv2
    from app.pipeline import omr_template as omr

    path = _upload_path(body.blank_url)
    if not os.path.exists(path) or os.path.splitext(path)[1].lower() not in (".png", ".jpg", ".jpeg"):
        raise HTTPException(status_code=400, detail="Upload the blank OMR sheet as a PNG or JPG first.")
    blank = cv2.imread(path)
    tpl = await asyncio.to_thread(omr.build_template, blank, body.mcq_count, body.n_options)
    if not tpl["bubbles"]:
        raise HTTPException(status_code=422, detail="No answer bubbles found on this sheet.")

    # Labelled preview the teacher checks before saving the paper
    preview = os.path.splitext(path)[0] + "_omrmap.png"
    cv2.imwrite(preview, omr.preview(blank, tpl))
    tpl["blank_url"] = body.blank_url
    return {"template": tpl, "preview_url": f"/api/papers/files/{os.path.basename(preview)}"}


# ── Release results to students (teacher only) ───────────────────────────────

class ReleaseRequest(BaseModel):
    released: bool


@router.put("/{paper_id}/release")
async def release_results(paper_id: str, body: ReleaseRequest, user: dict = Depends(require_teacher)):
    """Release the paper's results to students (or withdraw the release)."""
    pid = _valid_id(paper_id)
    upd = {"resultsReleased": body.released, "releasedAt": datetime.now(timezone.utc).isoformat() if body.released else None}
    res = await papers_col().update_one({"_id": pid, "teacher_id": user["sub"]}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found or not owned by you.")
    return {"id": paper_id, **upd}


# ── Optional RAG answer-key assistant: drafts only, the teacher edits; never used to grade students ──

class DraftAnswerKeyRequest(BaseModel):
    reference_urls: list[str]          # files from /papers/files/upload (PDF with a text layer, or .txt)
    questions: list[str]               # subjective question texts, in order
    marks: list[float] = []            # marks per question (default 1 each)


@router.post("/answer-key/draft")
async def draft_answer_key(body: DraftAnswerKeyRequest, user: dict = Depends(require_teacher)):
    """Reference answer + rubric points per question, each point citing the reference passages it came from."""
    import asyncio
    from app.pipeline import llm
    from app.services import answer_key as ak

    paths = [_upload_path(u) for u in body.reference_urls]
    missing = [os.path.basename(p) for p in paths if not os.path.exists(p)]
    if missing:
        raise HTTPException(status_code=404, detail=f"Reference file(s) not found: {', '.join(missing)} — upload them first.")
    ep = llm.resolve("grader") or llm.resolve("transcriber_a")
    if ep is None:
        raise HTTPException(status_code=503, detail="No language model is running right now; try again later.")
    passages = ak.chunk(await asyncio.to_thread(ak.load_reference, paths))
    skipped = list(ak.load_reference.last_skipped)
    if not passages:
        raise HTTPException(status_code=422, detail="No readable text in the reference files (scanned PDFs need a text layer).")

    # One draft per question, in parallel
    marks = [body.marks[i] if i < len(body.marks) else 1.0 for i in range(len(body.questions))]
    drafts = await asyncio.gather(*[asyncio.to_thread(ak.draft, ep, q, m, passages)
                                    for q, m in zip(body.questions, marks)])
    return {"drafts": [{"question": q, **d} for q, d in zip(body.questions, drafts)],
            "skipped_pages": skipped, "passages": len(passages)}


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
